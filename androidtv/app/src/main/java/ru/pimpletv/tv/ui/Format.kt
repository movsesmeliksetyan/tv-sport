package ru.pimpletv.tv.ui

import ru.pimpletv.tv.data.MatchSummary

/** "2026-06-05T20:00:00+03:00" -> "20:00". Cheap substring, no date lib needed. */
fun MatchSummary.kickoffTime(): String {
    val t = kickoff.substringAfter('T', "")
    return if (t.length >= 5) t.substring(0, 5) else kickoff
}

fun MatchSummary.matchTitle(): String = "${home.name} – ${away.name}"

fun MatchSummary.isLive(): Boolean = hasStream || status == "live"
