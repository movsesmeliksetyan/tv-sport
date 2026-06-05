package ru.pimpletv.tv.data

import com.google.gson.annotations.SerializedName

/** DTOs mirroring docs/api/openapi.yaml. Kept deliberately tolerant of nulls. */

data class MatchListResponse(
    @SerializedName("matches") val matches: List<MatchSummary> = emptyList(),
    @SerializedName("lastUpdated") val lastUpdated: String? = null,
)

data class Team(
    @SerializedName("name") val name: String,
    @SerializedName("logo") val logo: String? = null,
)

data class Stream(
    @SerializedName("type") val type: String = "acestream",
    @SerializedName("contentId") val contentId: String,
    @SerializedName("quality") val quality: String? = null,
    @SerializedName("language") val language: String? = null,
)

open class MatchSummary(
    @SerializedName("id") val id: String,
    @SerializedName("sport") val sport: String,
    @SerializedName("tournament") val tournament: String? = null,
    @SerializedName("home") val home: Team,
    @SerializedName("away") val away: Team,
    @SerializedName("kickoff") val kickoff: String,
    @SerializedName("channel") val channel: String? = null,
    @SerializedName("status") val status: String = "scheduled",
    @SerializedName("hasStream") val hasStream: Boolean = false,
    @SerializedName("lastUpdated") val lastUpdated: String? = null,
)

class Match(
    id: String,
    sport: String,
    tournament: String?,
    home: Team,
    away: Team,
    kickoff: String,
    channel: String?,
    status: String,
    hasStream: Boolean,
    lastUpdated: String?,
    @SerializedName("stadium") val stadium: String? = null,
    @SerializedName("streams") val streams: List<Stream> = emptyList(),
) : MatchSummary(id, sport, tournament, home, away, kickoff, channel, status, hasStream, lastUpdated)
