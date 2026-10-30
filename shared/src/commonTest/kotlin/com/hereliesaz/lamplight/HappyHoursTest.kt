package com.hereliesaz.lamplight

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class HappyHoursTest {
    private val header = "venue_id,venue,neighborhood,address,days_and_hours,drinks,food,restrictions,verification,source_url,research_date,notes"

    @Test fun parsesQuotedCommasAndEscapedQuotes() {
        val data = header + "\n" +
            "\"test\",\"Test, Bar\",\"French Quarter\",\"1 Main St\",\"Mon-Fri, 3-6 PM\",\"$5 \"\"special\"\"\",\"$6 bites\",\"Bar only\",\"researched\",\"https://example.com\",\"2026-10-29\",\"\"\n"
        val records = HappyHours.parse(data)
        assertEquals(1, records.size)
        assertEquals("Test, Bar", records[0].venue)
        assertEquals("$5 \"special\"", records[0].drinks)
    }

    @Test fun rejectsInvalidHeaderAndTruncatedRecords() {
        assertTrue(HappyHours.parse("bad,header\na,b").isEmpty())
        assertTrue(HappyHours.parse(header + "\nshort,row").isEmpty())
    }
}
