package ru.pimpletv.tv.data

/** Thin repository over the API. Phase 3 (T3.5) adds lifecycle-aware polling. */
class MatchRepository(private val service: ApiService = ApiClient.service) {

    suspend fun matches(sport: String? = null): List<MatchSummary> =
        service.listMatches(sport = sport).matches

    suspend fun match(id: String): Match = service.getMatch(id)
}
