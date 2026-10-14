from datetime import datetime, timezone

from fastapi import HTTPException


class NotificationService:
    """Read a company's actual certificate events; persist only read receipts."""

    def __init__(self, database):
        self.certificates = database.get_collection('certificates')
        self.reads = database.get_collection('notification_reads')

    def _pipeline(self, owner):
        certificate_id = {'$toString': '$_id'}
        description = {
            '$concat': [
                {'$ifNull': ['$participant_name', 'Participante']},
                ' — ',
                {'$ifNull': ['$event_name', 'Certificado']},
            ]
        }
        href = {'$concat': ['/certificados/visualizar/', certificate_id]}

        return [
            {'$match': {'issuer_id': owner, 'issued_at': {'$ne': None}}},
            {'$addFields': {'events': ['issued', 'sent', 'failed']}},
            {'$unwind': '$events'},
            {
                '$match': {
                    '$or': [
                        {'events': 'issued'},
                        {
                            'events': 'sent',
                            'notifications.student.status': 'sent',
                            'notifications.student.sent_at': {'$ne': None},
                        },
                        {
                            'events': 'failed',
                            'notifications.student.status': 'failed',
                            'notifications.student.claimed_at': {'$ne': None},
                        },
                    ]
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'id': {
                        '$concat': [
                            certificate_id,
                            ':',
                            '$events',
                            {
                                '$cond': [
                                    {'$eq': ['$events', 'failed']},
                                    {
                                        '$concat': [
                                            ':',
                                            {
                                                '$toString': {
                                                    '$ifNull': [
                                                        '$notifications.student.attempts',
                                                        0,
                                                    ],
                                                }
                                            },
                                        ]
                                    },
                                    '',
                                ],
                            },
                        ]
                    },
                    'type': {'$literal': 'certificate'},
                    'severity': {
                        '$cond': [
                            {'$eq': ['$events', 'failed']},
                            'warning',
                            'info',
                        ]
                    },
                    'title': {
                        '$switch': {
                            'branches': [
                                {
                                    'case': {'$eq': ['$events', 'sent']},
                                    'then': 'Envio de certificado aceito pelo servidor',
                                },
                                {
                                    'case': {'$eq': ['$events', 'failed']},
                                    'then': 'Falha no envio do certificado',
                                },
                            ],
                            'default': 'Certificado emitido',
                        }
                    },
                    'created_at': {
                        '$switch': {
                            'branches': [
                                {
                                    'case': {'$eq': ['$events', 'sent']},
                                    'then': '$notifications.student.sent_at',
                                },
                                {
                                    'case': {'$eq': ['$events', 'failed']},
                                    'then': '$notifications.student.claimed_at',
                                },
                            ],
                            'default': '$issued_at',
                        }
                    },
                    'description': description,
                    'href': href,
                }
            },
            {'$addFields': {'receipt_id': {'$concat': [owner, ':', '$id']}}},
            {
                '$lookup': {
                    'from': 'notification_reads',
                    'localField': 'receipt_id',
                    'foreignField': '_id',
                    'as': 'receipts',
                }
            },
            {'$addFields': {'read': {'$gt': [{'$size': '$receipts'}, 0]}}},
            {'$project': {'receipts': 0, 'receipt_id': 0}},
        ]

    async def list(self, owner, page=1, limit=5):
        pipeline = self._pipeline(owner) + [
            {
                '$addFields': {
                    'priority': {
                        '$cond': [
                            {
                                '$and': [
                                    {'$eq': ['$severity', 'warning']},
                                    {'$eq': ['$read', False]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                }
            },
            {'$sort': {'priority': -1, 'created_at': -1, 'id': 1}},
            {'$project': {'priority': 0}},
            {
                '$facet': {
                    'items': [
                        {'$skip': (page - 1) * limit},
                        {'$limit': limit},
                    ],
                    'total': [{'$count': 'count'}],
                    'unread': [
                        {'$match': {'read': False}},
                        {'$count': 'count'},
                    ],
                }
            },
        ]
        result = (await self.certificates.aggregate(pipeline).to_list(1))[0]
        total = result['total'][0]['count'] if result['total'] else 0
        unread = result['unread'][0]['count'] if result['unread'] else 0
        return {
            'items': result['items'],
            'total': total,
            'unread_count': unread,
            'page': page,
            'total_pages': (total + limit - 1) // limit,
        }

    async def mark_read(self, owner, notification_id):
        items = await self.certificates.aggregate(
            self._pipeline(owner) + [{'$match': {'id': notification_id}}]
        ).to_list(1)
        if not items:
            raise HTTPException(404, 'Notificação não encontrada.')
        await self._save_receipt(owner, notification_id)
        return {**items[0], 'read': True}

    async def _save_receipt(self, owner, notification_id):
        result = await self.reads.update_one(
            {'_id': f'{owner}:{notification_id}'},
            {
                '$setOnInsert': {
                    'owner_id': owner,
                    'read_at': datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        return int(result.upserted_id is not None)

    async def mark_all_read(self, owner):
        # Snapshot the current unread events before writing any receipts.
        events = await self.certificates.aggregate(
            self._pipeline(owner)
            + [
                {'$match': {'read': False}},
                {'$project': {'id': 1}},
            ]
        ).to_list(None)
        updated = 0
        for event in events:
            updated += await self._save_receipt(owner, event['id'])
        return updated
