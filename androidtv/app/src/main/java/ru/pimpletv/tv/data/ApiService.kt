package ru.pimpletv.tv.data

import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

/** Retrofit interface for the backend (docs/api/openapi.yaml). */
interface ApiService {

    @GET("api/matches")
    suspend fun listMatches(
        @Query("sport") sport: String? = null,
        @Query("window") window: String = "today",
    ): MatchListResponse

    @GET("api/matches/{id}")
    suspend fun getMatch(@Path("id") id: String): Match
}
