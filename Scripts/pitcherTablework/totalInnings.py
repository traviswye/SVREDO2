def calculate_totals(data):
    totals = {
        "Split": "Full",
        "G": int(data[0][1]),  # Use the first inning's G value
        "IP": 0, "ER": 0, "PA": 0, "AB": 0, "R": 0, "H": 0,
        "2B": 0, "3B": 0, "HR": 0, "SB": 0, "CS": 0, "BB": 0, "SO": 0,
        "TB": 0, "GDP": 0, "HBP": 0, "SH": 0, "SF": 0, "IBB": 0, "ROE": 0,
        "BAbip": 0
    }
    total_outs = 0
    total_singles = 0
    total_on_base = 0
    total_bip = 0  # Balls in play for BAbip calculation

    for row in data:
        totals["ER"] += int(row[3])
        totals["PA"] += int(row[5])
        totals["AB"] += int(row[6])
        totals["R"] += int(row[7])  # Fixing this part to ensure correct addition of runs
        totals["H"] += int(row[8])
        totals["2B"] += int(row[9])
        totals["3B"] += int(row[10])
        totals["HR"] += int(row[11])
        totals["SB"] += int(row[12])
        totals["CS"] += int(row[13])
        totals["BB"] += int(row[14])
        totals["SO"] += int(row[15])
        totals["TB"] += int(row[20])
        totals["GDP"] += int(row[21])
        totals["HBP"] += int(row[22])
        totals["SH"] += int(row[23])
        totals["SF"] += int(row[24])
        totals["IBB"] += int(row[25])
        totals["ROE"] += int(row[26])

        # Calculate total singles for SLG calculation
        total_singles += int(row[8]) - int(row[9]) - int(row[10]) - int(row[11])

        # Track outs for innings pitched calculation
        ip_parts = str(row[2]).split('.')
        outs = int(ip_parts[0]) * 3  # Full innings converted to outs
        if len(ip_parts) > 1:
            outs += int(ip_parts[1])  # Add remaining outs (1 out = .1, 2 outs = .2)
        total_outs += outs

        # Calculate total on-base occurrences for OBP calculation
        total_on_base += int(row[8]) + int(row[14]) + int(row[22])  # H + BB + HBP

        # Calculate total balls in play for BAbip calculation
        total_bip += int(row[6]) - int(row[15]) - int(row[11]) + int(row[24])  # AB - SO - HR + SF

    # Convert outs to innings pitched
    full_innings = total_outs // 3
    remaining_outs = total_outs % 3
    totals["IP"] = f"{full_innings}.{remaining_outs}"

    # Calculate derived statistics
    if totals["AB"] > 0:
        totals["BA"] = round(totals["H"] / totals["AB"], 3)
        totals["SLG"] = round((total_singles + (2 * totals["2B"]) + (3 * totals["3B"]) + (4 * totals["HR"])) / totals["AB"], 3)

    if totals["PA"] > 0:
        totals["OBP"] = round((totals["H"] + totals["BB"] + totals["HBP"]) / totals["PA"], 3)
        totals["OPS"] = round(totals["OBP"] + totals["SLG"], 3)

    if totals["BB"] > 0:
        totals["SO/W"] = round(totals["SO"] / totals["BB"], 2)

    if total_bip > 0:
        totals["BAbip"] = round((totals["H"] - totals["HR"]) / total_bip, 3)

    # Calculate ERA from ER and IP
    if total_outs > 0:
        totals["ERA"] = round((totals["ER"] * 9) / (total_outs / 3), 2)

    return totals

# Example data (as provided)
inning_data = [
    ["1st inning", 22, 22.0, 7, 2.86, 90, 81, 7, 22, 4, 0, 0, 5, 1, 6, 24, 4.00, .272, .322, .321, 26, 2, 1, 0, 2, 0, 0, .373],
    ["2nd inning", 22, 22.0, 10, 4.09, 91, 85, 13, 21, 4, 0, 2, 0, 0, 5, 20, 4.00, .247, .286, .365, 31, 4, 0, 0, 1, 0, 1, .297],
    ["3rd inning", 22, 22.0, 7, 2.86, 79, 72, 7, 13, 3, 1, 1, 0, 0, 4, 18, 4.50, .181, .228, .292, 21, 5, 1, 0, 2, 0, 0, .218],
    ["4th inning", 22, 22.0, 4, 1.64, 82, 74, 4, 17, 4, 0, 0, 1, 0, 6, 13, 2.17, .230, .293, .284, 21, 8, 1, 0, 1, 0, 0, .274],
    ["5th inning", 21, 20.1, 13, 5.75, 90, 81, 12, 21, 2, 0, 4, 1, 0, 8, 33, 4.13, .259, .333, .432, 35, 2, 1, 0, 0, 0, 1, .386],
    ["6th inning", 17, 15.2, 5, 2.87, 62, 54, 5, 8, 1, 0, 3, 0, 0, 7, 14, 2.00, .148, .258, .333, 18, 2, 1, 0, 0, 0, 1, .135],
    ["7th inning", 10, 9.1, 1, 0.96, 39, 35, 1, 10, 0, 0, 0, 0, 0, 4, 7, 1.75, .286, .359, .286, 10, 3, 0, 0, 0, 0, 0, .357],
    ["8th inning", 3, 2.2, 0, 0.00, 9, 9, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, .111, .111, .111, 1, 0, 0, 0, 0, 0, 0, .125],
    ["9th inning", 2, 1.2, 2, 10.80, 8, 5, 2, 1, 0, 0, 1, 0, 0, 3, 1, 0.33, .200, .500, .800, 4, 1, 0, 0, 0, 0, 0, .000]
]

totals = calculate_totals(inning_data)
print(totals)
