#!/usr/bin/env python

import json
import logging

from graphql import GraphQLError, ExecutionResult
from graphql.pyutils import EventEmitter
from sanic import Sanic
from sanic.response import html, json as json_response

from examples.library.mutation import Mutation
from examples.library.query import Query
from examples.library.subscription import Subscription
from examples.library.template import TEMPLATE
from typegql.core.schema import Schema

logger = logging.getLogger('sanic.error')
app = Sanic(name='TypeGQL')
schema = Schema(query=Query, mutation=Mutation, subscription=Subscription)
channels = {'books': EventEmitter()}


@app.route('', methods=['GET'])
async def graphiql(request):
    return html(TEMPLATE)


@app.route('/graphql', methods=['POST'])
async def graphql(request):
    query = request.args.get('query') if request.method.lower() == 'get' else request.json.get('query')
    operation_name = request.json.get('operationName')
    try:
        result = await schema.run(query, operation=operation_name, context={'pubsub': channels})
    except GraphQLError as e:
        logger.exception(e)
        return json_response({'data': str(e)})
    if result.errors:
        for error in result.errors:
            logger.exception(error)
        return json_response({'data': [str(e) for e in result.errors]}, status=401)
    return json_response({'data': result.data})


@app.websocket('/graphql')
async def subscription(_, ws):
    _ = json.loads(await ws.recv())
    data = json.loads(await ws.recv())
    result = await schema.subscribe(
        query=data['payload']['query'],
        operation=data['payload']['operationName'],
        variables=data['payload']['variables'])

    async for message in result:  # type: ExecutionResult
        _type = 'data'
        payload = message._asdict()
        if message.errors:
            _type = 'error'
            payload['errors'] = [e.formatted for e in message.errors]
        result = json.dumps({'id': data['id'], 'type': _type, 'payload': payload})
        await ws.send(result)


if __name__ == '__main__':
    app.run(host='localhost', port=3000, debug=True, auto_reload=False)
