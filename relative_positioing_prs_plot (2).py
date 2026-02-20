# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 13:53:00 2025

@author: HP
"""

import matplotlib.pyplot as plt
import numpy as np

LOG_FILE = "prs_log.txt"

# Path loss model parameters
P_tx = 43      # dBm, assumed tower transmit power
PL0 = 32.4     # Free space path loss @ 1 m
n = 3.5        # Path loss exponent (urban ~3–4)

def estimate_distance(rsrp_dbm):
    """Estimate distance (m) from RSRP using path loss model."""
    try:
        rsrp_dbm = float(rsrp_dbm)
        PL = P_tx - rsrp_dbm
        d = 10 ** ((PL - PL0) / (10 * n))
        return round(d, 2)
    except:
        return None

def parse_log(file_path):
    towers = []
    with open(file_path, "r") as f:
        for line in f:
            if "+QENG:" in line and "servingcell" in line:
                parts = [p.strip().replace('"', '') for p in line.split(",")]
                try:
                    rsrp = parts[14] if len(parts) > 14 else None
                    towers.append({
                        "type": "serving",
                        "id": parts[6],   # Cell ID (hex)
                        "rsrp": rsrp,
                        "distance": estimate_distance(rsrp)
                    })
                except Exception as e:
                    print("Parse fail (serving):", e)

            elif "+QENG:" in line and "neighbourcell" in line:
                parts = [p.strip().replace('"', '') for p in line.split(",")]
                try:
                    pci = parts[3]
                    rsrp = parts[5] if len(parts) > 5 else None
                    towers.append({
                        "type": "neighbour",
                        "id": f"PCI-{pci}",
                        "rsrp": rsrp,
                        "distance": estimate_distance(rsrp)
                    })
                except Exception as e:
                    print("Parse fail (neighbour):", e)
    return [t for t in towers if t["distance"] is not None]

def place_towers(n_towers, radius=500):
    """Place towers in a circle for visualization (no real lat/lon)."""
    angles = np.linspace(0, 2*np.pi, n_towers, endpoint=False)
    return [(radius*np.cos(a), radius*np.sin(a)) for a in angles]

def estimate_position(tower_positions, distances):
    """Estimate device position as centroid of circle intersections."""
    xs, ys = [], []
    for (x, y), d in zip(tower_positions, distances):
        xs.append(x + d * np.cos(np.random.rand()*2*np.pi))
        ys.append(y + d * np.sin(np.random.rand()*2*np.pi))
    return np.mean(xs), np.mean(ys)

def plot_map(towers, est_pos, true_pos=None):
    plt.figure(figsize=(6,6))

    # Place towers in circle
    tower_positions = place_towers(len(towers), radius=500)

    for i, (tower, (x, y)) in enumerate(zip(towers, tower_positions)):
        d = tower["distance"]
        plt.scatter(x, y, c="blue", marker="^", s=100, label="Tower" if i==0 else "")
        circle = plt.Circle((x, y), d, color="blue", alpha=0.1)
        plt.gca().add_patch(circle)
        plt.text(x, y+50, f"{tower['id']}\n{int(d)}m", ha="center", fontsize=8)

    # Estimated device
    plt.scatter(est_pos[0], est_pos[1], c="red", marker="o", s=120, label="Estimated Device")

    # Ground truth if provided
    if true_pos:
        plt.scatter(true_pos[0], true_pos[1], c="green", marker="x", s=120, label="GPS Truth")
        error = np.sqrt((est_pos[0]-true_pos[0])**2 + (est_pos[1]-true_pos[1])**2)
        plt.title(f"Relative Device Position (Error ≈ {error:.1f} m)")
    else:
        plt.title("Relative Device Position (no GPS reference)")

    plt.axhline(0, color="gray", lw=0.5)
    plt.axvline(0, color="gray", lw=0.5)
    plt.legend()
    plt.axis("equal")
    plt.show()

def main():
    towers = parse_log(LOG_FILE)
    if len(towers) < 2:
        print("⚠️ Not enough towers for relative positioning.")
        return

    distances = [t["distance"] for t in towers]
    tower_positions = place_towers(len(towers), radius=500)
    est_pos = estimate_position(tower_positions, distances)

    print("\n📡 Relative Tower Distances:")
    for t in towers:
        print(f"{t['type']:9s} {t['id']:10s} | RSRP: {t['rsrp']:>5s} dBm | ~{t['distance']} m")

    # GPS truth position (optional: replace with AT+QGPSLOC result)
    true_pos = None
    print(est_pos)
    plot_map(towers, est_pos, true_pos)

if __name__ == "__main__":
    main()
