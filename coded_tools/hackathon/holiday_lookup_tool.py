"""
holiday_lookup_tool.py
Looks up office holidays from the office_holidays table for a given location/city.
"""
import sqlite3
import os
from typing import Any

_HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get(
    "HACKATHON_DB",
    os.path.normpath(os.path.join(_HERE, "..", "..", "database", "hackathon", "hackathon.db"))
)


class HolidayLookupTool:
    """Returns office holidays and office address for a given location."""

    def get_instructions(self) -> str:
        return (
            "Use this tool to look up Cognizant office holidays for a specific location. "
            "Provide 'location' (city name e.g. 'Bangalore', 'Chennai', 'Atlanta') "
            "or 'associate_id' to auto-detect from the associate's city. "
            "Returns holiday list and office address details."
        )

    def invoke(self, args: dict[str, Any]) -> dict[str, Any]:
        location = str(args.get("location", "")).strip()
        associate_id = args.get("associate_id")

        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row

            # Auto-detect location from associate city if not provided
            if not location and associate_id:
                row = conn.execute(
                    "SELECT city FROM associates WHERE associate_id = ?",
                    (int(associate_id),)
                ).fetchone()
                if row:
                    location = row["city"]

            if not location:
                conn.close()
                return {"error": "Please provide a location (city) or associate_id"}

            # Match location_code or city (case-insensitive)
            holidays = conn.execute(
                """SELECT id, location_code, holiday_date, holiday_name,
                          office_name, office_address, city, state_province
                   FROM office_holidays
                   WHERE (LOWER(location_code) = LOWER(?) OR LOWER(city) LIKE LOWER(?))
                     AND is_active = 1
                   ORDER BY holiday_date""",
                (location, f"%{location}%")
            ).fetchall()

            # Also fetch ALL (national holidays for India or USA)
            # Determine region
            region_check = conn.execute(
                "SELECT region, country FROM office_holidays WHERE LOWER(city) LIKE LOWER(?) LIMIT 1",
                (f"%{location}%",)
            ).fetchone()

            national_code = "ALL" if (region_check and region_check["country"] == "India") else "USA_ALL"
            national = conn.execute(
                """SELECT id, location_code, holiday_date, holiday_name
                   FROM office_holidays
                   WHERE location_code = ? AND is_active = 1
                   ORDER BY holiday_date""",
                (national_code,)
            ).fetchall()

            conn.close()

            if not holidays and not national:
                return {
                    "location": location,
                    "message": f"No holidays found for '{location}'. "
                               f"Available India locations: Bangalore, Chennai, Hyderabad, Pune, Mumbai, "
                               f"Noida, Gurgaon, Kolkata, Kochi, Coimbatore, Indore, Mangalore, "
                               f"Bhubaneswar, Visakhapatnam, Ahmedabad. "
                               f"Americas: Teaneck, Atlanta, Dallas, Chicago, New York, etc."
                }

            office_info = None
            if holidays:
                h = dict(holidays[0])
                office_info = {
                    "office_name": h["office_name"],
                    "office_address": h["office_address"],
                    "city": h["city"],
                    "state_province": h["state_province"],
                }

            location_holidays = [
                {"date": h["holiday_date"], "name": h["holiday_name"]}
                for h in holidays
            ]
            national_holidays = [
                {"date": h["holiday_date"], "name": h["holiday_name"]}
                for h in national
            ]

            # Merge and deduplicate
            all_dates = {h["date"] for h in location_holidays}
            combined = location_holidays + [h for h in national_holidays if h["date"] not in all_dates]
            combined.sort(key=lambda x: x["date"])

            return {
                "location": location,
                "office_info": office_info,
                "total_holidays": len(combined),
                "holidays": combined,
                "national_holidays_count": len(national_holidays),
                "location_specific_count": len(location_holidays),
            }
        except Exception as e:
            return {"error": str(e)}
