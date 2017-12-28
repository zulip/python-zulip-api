link_query = 'SELECT {} FROM {} WHERE Id=\'{}\''
default_query = 'SELECT {} FROM {} WHERE Name LIKE \'%{}%\' LIMIT {}'

commands = [
    {
        'commands': ['search account', 'find account', 'search accounts', 'find accounts'],
        'object': 'account',
        'description': 'Returns a list of accounts of the name specified',
        'template': 'search account <name>'
    },
    {
        'commands': ['search contact', 'find contact', 'search contacts', 'find contacts'],
        'object': 'contact',
        'description': 'Returns a list of contacts of the name specified',
        'template': 'search contact <name>'
    },
    {
        'commands': ['search opportunity', 'find opportunity', 'search opportunities', 'find opportunities'],
        'object': 'opportunity',
        'description': 'Returns a list of opportunities of the name specified',
        'template': 'search opportunity <name>'
    },
    {
        'commands': ['search top opportunity', 'find top opportunity', 'search top opportunities', 'find top opportunities'],
        'object': 'opportunity',
        'query': 'SELECT {} FROM {} WHERE isClosed=false ORDER BY amount DESC LIMIT {}',
        'description': 'Returns a list of opportunities organised by amount',
        'template': 'search top opportunities <amount>',
        'rank_output': True,
        'force_keys': ['Amount']
    }
]  # type: List[Dict[str, Any]]

object_types = {
    'account': {
        'fields': 'Id, Name, Phone, BillingStreet, BillingCity, BillingState',
        'table': 'Account'
    },
    'contact': {
        'fields': 'Id, Name, Phone, MobilePhone, Email',
        'table': 'Contact'
    },
    'opportunity': {
        'fields': 'Id, Name, Amount, Probability, StageName, CloseDate',
        'table': 'Opportunity'
    }
}  # type: Dict[str, Dict[str, str]]
