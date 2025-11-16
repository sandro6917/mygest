from __future__ import annotations

import graphene

from comunicazioni.schema import Query as ComunicazioniQuery, Mutation as ComunicazioniMutation


class Query(ComunicazioniQuery, graphene.ObjectType):
    pass


class Mutation(ComunicazioniMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
