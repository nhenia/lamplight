package com.hereliesaz.lamplight

import lamplight.shared.generated.resources.Res

data class HappyHour(
    val venueId: String,
    val venue: String,
    val neighborhood: String,
    val address: String,
    val daysAndHours: String,
    val drinks: String,
    val food: String,
    val restrictions: String,
    val verification: String,
    val sourceUrl: String,
    val researchDate: String,
    val notes: String
)

private val HAPPY_HOUR_HEADERS = listOf(
    "venue_id", "venue", "neighborhood", "address", "days_and_hours",
    "drinks", "food", "restrictions", "verification", "source_url", "research_date", "notes"
)

object HappyHours {
    const val URL = "https://raw.githubusercontent.com/nhenia/lamplight/main/shared/src/commonMain/composeResources/files/happy_hours_tinyfish_2026_10_22.csv"
    const val CACHE_KEY = "happy_hours_live_csv"
    private const val BUNDLED = "files/happy_hours_tinyfish_2026_10_22.csv"

    fun parse(csv: String): List<HappyHour> {
        val rows = runCatching { parseCsv(csv.removePrefix("\uFEFF")) }.getOrElse { return emptyList() }
        if (rows.firstOrNull() != HAPPY_HOUR_HEADERS) return emptyList()
        return rows.drop(1).filter { it.size == 12 && it[1].isNotBlank() }.map {
            HappyHour(it[0], it[1], it[2], it[3], it[4], it[5],
                it[6], it[7], it[8], it[9], it[10], it[11])
        }
    }

    suspend fun loadFallback(): List<HappyHour> =
        runCatching { parse(Res.readBytes(BUNDLED).decodeToString()) }.getOrElse { emptyList() }
}

/** Platform HTTP implementation; null means offline, unavailable, or not supported. */
internal expect suspend fun fetchHappyHourCsv(url: String): String?
