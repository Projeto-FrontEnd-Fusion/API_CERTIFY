from datetime import datetime, timezone


class DashboardService:
    def __init__(self, database):
        self.certificates = database.get_collection('certificates')

    async def summary(self, owner, now=None):
        now = now or datetime.now(timezone.utc)
        months = []
        for offset in range(5, -1, -1):
            index = now.year * 12 + now.month - 1 - offset
            months.append(f'{index // 12:04d}-{index % 12 + 1:02d}')
        start = datetime.fromisoformat(months[0] + '-01').replace(
            tzinfo=timezone.utc
        )
        pipeline = [
            {'$match': {'issuer_id': owner, 'issued_at': {'$ne': None}}},
            {
                '$facet': {
                    'issued': [{'$count': 'value'}],
                    'sent': [
                        {'$match': {'notifications.student.status': 'sent'}},
                        {'$count': 'value'},
                    ],
                    'pending_delivery': [
                        {
                            '$match': {
                                'notifications.student.status': {
                                    '$in': [
                                        'pending',
                                        'sending',
                                        'failed',
                                        'deferred',
                                    ]
                                }
                            }
                        },
                        {'$count': 'value'},
                    ],
                    'participants': [
                        {
                            '$project': {
                                'email': {
                                    '$toLower': {
                                        '$ifNull': ['$participant_email', '']
                                    }
                                }
                            }
                        },
                        {'$match': {'email': {'$ne': ''}}},
                        {'$group': {'_id': '$email'}},
                    ],
                    'emissions': [
                        {
                            '$match': {
                                'issued_at': {'$gte': start, '$lte': now}
                            }
                        },
                        {
                            '$group': {
                                '_id': {
                                    '$dateToString': {
                                        'format': '%Y-%m',
                                        'date': '$issued_at',
                                    }
                                },
                                'emissions': {'$sum': 1},
                            }
                        },
                    ],
                    'recent_activities': [
                        {'$sort': {'issued_at': -1, '_id': -1}},
                        {'$limit': 5},
                        {
                            '$project': {
                                '_id': 0,
                                'id': {'$toString': '$_id'},
                                'name': '$event_name',
                                'student': '$participant_name',
                                'issued_at': 1,
                            }
                        },
                    ],
                }
            },
        ]
        result = (await self.certificates.aggregate(pipeline).to_list(1))[0]
        counts = {
            key: result[key][0]['value'] if result[key] else 0
            for key in ('issued', 'sent', 'pending_delivery')
        }
        counts['participants'] = len(
            {
                item['_id'].strip()
                for item in result['participants']
                if item['_id'].strip()
            }
        )
        monthly = {
            item['_id']: item['emissions'] for item in result['emissions']
        }
        return {
            **counts,
            'emissions': [
                {'month': month, 'emissions': monthly.get(month, 0)}
                for month in months
            ],
            'recent_activities': result['recent_activities'],
        }
