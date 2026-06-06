package ru.pimpletv.tv.ui

import ru.pimpletv.tv.data.MatchSummary
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

private val DAY_FMT = DateTimeFormatter.ofPattern("EEE d MMM", Locale.ENGLISH)
private val TIME_FMT = DateTimeFormatter.ofPattern("HH:mm")

/** Device's configured time zone — all times/dates are shown relative to it. */
private fun zone(): ZoneId = ZoneId.systemDefault()

private fun MatchSummary.kickoffInstant(): OffsetDateTime? =
    runCatching { OffsetDateTime.parse(kickoff) }.getOrNull()

/** Kickoff time in the device's local zone, e.g. MSK "20:00+03:00" -> "21:00" in +04. */
fun MatchSummary.kickoffTime(): String =
    kickoffInstant()?.atZoneSameInstant(zone())?.format(TIME_FMT)
        ?: kickoff.substringAfter('T', "").take(5)

/** Kickoff calendar date in the device's local zone (used for day grouping). */
fun MatchSummary.kickoffDate(): LocalDate? =
    kickoffInstant()?.atZoneSameInstant(zone())?.toLocalDate()

fun MatchSummary.matchTitle(): String = "${home.name} – ${away.name}"

fun MatchSummary.isLive(): Boolean = hasStream || status == "live"

/** "Today" / "Tomorrow" / "Mon 8 Jun" relative to the device's current date. */
fun dayLabel(date: LocalDate, today: LocalDate = LocalDate.now(zone())): String = when (date) {
    today -> "Today"
    today.plusDays(1) -> "Tomorrow"
    else -> date.format(DAY_FMT)
}

fun today(): LocalDate = LocalDate.now(zone())
