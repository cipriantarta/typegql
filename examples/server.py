import logging

from graphql import GraphQLError
from sanic import Sanic
from sanic.response import json, html

from typegql.core.schema import Schema
from examples.library.query import Query, Mutation

from examples.library.template import TEMPLATE

logger = logging.getLogger('sanic.error')
app = Sanic()
schema = Schema(Query, Mutation)


@app.route('', methods=['GET'])
async def default(request):
    return html(TEMPLATE)


@app.route('/graphql', methods=['POST'])
async def default(request):
    query = request.args.get('query') if request.method.lower() == 'get' else request.json.get('query')
    operation_name = request.json.get('operationName')
    try:
        result = await schema.run(query, operation=operation_name)
    except GraphQLError as e:
        logger.exception(e)
        return json({'data': str(e)})
    if result.errors:
        for error in result.errors:
            logger.exception(error)
        return json({'data': [str(e) for e in result.errors]}, status=401)
    return json({'data': result.data})


if __name__ == '__main__':
    app.run(host='localhost', port=3000, debug=True, auto_reload=False)
