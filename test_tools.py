from app.tools import call_tool, free_look_calculator

# Online purchase on 20 Oct 2026: 30 days -> 19 Nov 2026
r = free_look_calculator("2026-10-20", "electronic", 18500, today="2026-11-01")
assert r["last_date"] == "2026-11-19", r
assert r["days_allowed"] == 30
assert r["within_window"] is True and r["days_left"] == 18
assert r["estimated_refund"] == 18500.0

# Deductions are subtracted: 500 + 150 + 200 = 850
r = free_look_calculator("2026-10-20", "electronic", 18500, 500, 150, 200, today="2026-11-01")
assert r["total_deductions"] == 850.0 and r["estimated_refund"] == 17650.0

# Offline sale: 15 days, and the window can be over
r = free_look_calculator("2026-11-10", "offline", 10000, today="2026-11-30")
assert r["last_date"] == "2026-11-25"
assert r["within_window"] is False and r["days_left"] == -5

# Deductions larger than the premium never give a negative refund
r = free_look_calculator("2026-10-20", "distance", 1000, 800, 500, today="2026-11-01")
assert r["estimated_refund"] == 0.0

# Bad input returns an error instead of crashing
bad = call_tool("free_look_calculator",
                {"received_date": "2026-10-20", "sold_via": "online", "premium": 1000})
assert bad["ok"] is False and "offline" in bad["error"], bad
assert call_tool("free_look_calculator", {"received_date": "20/10/2026", "sold_via": "offline", "premium": 1})["ok"] is False
assert call_tool("free_look_calculator", {"received_date": "2026-10-20", "sold_via": "offline"})["ok"] is False
assert call_tool("free_look_calculator", {"received_date": "2026-10-20", "sold_via": "offline", "premium": -5})["ok"] is False
assert call_tool("no_such_tool", {})["ok"] is False
assert call_tool("free_look_calculator", {"received_date": "2026-10-20", "sold_via": "offline",
                                          "premium": 1000, "today": "2030-01-01"})["ok"] is False

print("all tool checks passed")