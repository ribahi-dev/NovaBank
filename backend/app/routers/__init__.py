"""Routers — la couche HTTP : routes, statuts, traduction des erreurs.

Règle de la couche : un router valide (via les schemas), délègue aux
services/requêtes, et traduit les résultats en réponses HTTP. AUCUNE
règle métier ici — elle vit dans services/.
"""
