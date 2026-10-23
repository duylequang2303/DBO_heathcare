"""Tự động kết xuất giao diện Web UI thực tế và chụp màn hình bằng Firefox Headless.

Đầu ra: experiments/ablation_dbo_idbo/fig_web_ui_actual_screenshot.png
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_PNG = ROOT / "experiments" / "ablation_dbo_idbo" / "fig_web_ui_actual_screenshot.png"
DEMO_HTML = ROOT / "app" / "static" / "demo_generated.html"

from app.api.services import generate_menu, PRESET_PROFILES, get_targets, build_profile
from app.api.schemas import GenerateIn, ProfileIn

def build_demo_page():
    # 1. Chạy solver tạo menu thật cho Profile P1
    pin = ProfileIn(**PRESET_PROFILES["p1"])
    req = GenerateIn(profile=pin, seed=9001, config="smoke")
    menu = generate_menu(req)

    prof = PRESET_PROFILES["p1"]
    targets = menu.targets
    totals = menu.totals

    # Nhóm món ăn theo bữa
    meals_dict = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
    meal_names = {"breakfast": "🌅 Bữa Sáng", "lunch": "☀️ Bữa Trưa", "dinner": "🌙 Bữa Tối", "snack": "🍎 Bữa Phụ"}
    for item in menu.items:
        mtype = item.meal_type if item.meal_type in meals_dict else "breakfast"
        meals_dict[mtype].append(item)

    # Render HTML các bữa ăn
    menu_rows_html = ""
    for mtype, items in meals_dict.items():
        if not items:
            continue
        menu_rows_html += f'<tr class="meal-header-row"><td colspan="8"><strong>{meal_names[mtype]}</strong></td></tr>'
        for it in items:
            menu_rows_html += f"""
            <tr>
              <td><span class="badge badge-meal">{it.slot}</span></td>
              <td style="max-width:280px;font-weight:500;">{it.name}</td>
              <td><span style="color:var(--text-3)">{it.portion_g:.0f}g</span></td>
              <td><strong style="color:var(--primary);font-size:1.05rem;">{it.portion_g_rounded}g</strong></td>
              <td>{it.macros.calories:.0f}</td>
              <td>{it.macros.protein_g:.1f}g</td>
              <td>{it.macros.carbs_g:.1f}g</td>
              <td>{it.macros.fat_g:.1f}g</td>
            </tr>
            """

    # Render Progress Bars
    nutrients = [
        ("Năng lượng", totals["calories"], targets["calories"], "kcal"),
        ("Protein", totals["protein_g"], targets["protein_g"], "g"),
        ("Carbohydrate", totals["carbs_g"], targets["carbs_g"], "g"),
        ("Chất béo (Lipid)", totals["fat_g"], targets["fat_g"], "g"),
        ("Chất xơ", totals["fiber_g"], targets["fiber_g"], "g"),
        ("Natri", totals["sodium_mg"], targets["sodium_mg"], "mg"),
    ]
    progress_html = ""
    for name, act, tgt, unit in nutrients:
        pct = (act / tgt) * 100 if tgt > 0 else 0
        status_color = "var(--success)" if 85 <= pct <= 115 else ("var(--warning)" if 75 <= pct <= 125 else "var(--danger)")
        progress_html += f"""
        <div class="progress-item" style="margin-bottom:12px;">
          <div style="display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:4px;">
            <span style="font-weight:600;color:var(--text-1);">{name}</span>
            <span style="color:var(--text-2);">{act:.0f} / {tgt:.0f} {unit} ({pct:.1f}%)</span>
          </div>
          <div style="background:rgba(255,255,255,0.08);border-radius:6px;height:8px;overflow:hidden;">
            <div style="background:{status_color};width:{min(pct, 100):.1f}%;height:100%;border-radius:6px;"></div>
          </div>
        </div>
        """

    # Đọc index.html gốc và thay thế trạng thái đã sinh menu
    with open(ROOT / "app" / "static" / "index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Điền giá trị form
    html = html.replace('id="inpName" class="form-control" type="text" placeholder="Nguyễn Văn A" value=""', 'id="inpName" class="form-control" type="text" value="Duy (P1)"')
    html = html.replace('id="inpAge" class="form-control" type="number"\n                     min="18" max="120" placeholder="25" value="25"', 'id="inpAge" class="form-control" type="number" value="22"')
    html = html.replace('id="inpHeight" class="form-control" type="number"\n                     min="100" max="250" step="0.1" placeholder="170" value="170"', 'id="inpHeight" class="form-control" type="number" value="170"')
    html = html.replace('id="inpWeight" class="form-control" type="number"\n                     min="30" max="400" step="0.1" placeholder="65" value="65"', 'id="inpWeight" class="form-control" type="number" value="65"')

    # Hiển thị targets bar
    targets_bar_content = f"""
    <div id="targetsBar" class="targets-bar" style="display:flex;gap:12px;margin-bottom:16px;">
      <div class="target-chip"><span class="target-chip-label">BMR</span><span class="target-chip-value">1618</span><span class="target-chip-unit">kcal</span></div>
      <div class="target-chip"><span class="target-chip-label">TDEE</span><span class="target-chip-value">2492</span><span class="target-chip-unit">kcal</span></div>
      <div class="target-chip"><span class="target-chip-label">Đạm</span><span class="target-chip-value">125</span><span class="target-chip-unit">g</span></div>
      <div class="target-chip"><span class="target-chip-label">Carbs</span><span class="target-chip-value">343</span><span class="target-chip-unit">g</span></div>
      <div class="target-chip"><span class="target-chip-label">Chất béo</span><span class="target-chip-value">69</span><span class="target-chip-unit">g</span></div>
      <div class="target-chip"><span class="target-chip-label">Chất xơ</span><span class="target-chip-value">35</span><span class="target-chip-unit">g</span></div>
    </div>
    """
    html = html.replace('<div id="targetsBar" class="targets-bar" style="display:none"\n           role="region" aria-label="Mục tiêu dinh dưỡng">\n        <!-- Filled by app.js -->\n      </div>', targets_bar_content)

    # Hiển thị menu section
    html = html.replace('<div id="menuSection">', '<div id="menuSection" style="display:block;">')
    html = html.replace('<div id="progressBars">\n                <!-- Filled by charts.js -->\n              </div>', f'<div id="progressBars">{progress_html}</div>')
    html = html.replace('<tbody id="menuTableBody">\n                <!-- Filled by app.js -->\n              </tbody>', f'<tbody id="menuTableBody">{menu_rows_html}</tbody>')
    html = html.replace('<div id="fitnessScore"></div>', f'<div id="fitnessScore"><span class="fitness-badge" style="background:rgba(33,122,75,0.25);color:#4ade80;padding:6px 14px;border-radius:20px;font-weight:700;font-size:1.1rem;border:1px solid #22c55e;">Điểm tối ưu: {menu.fitness:.2f}/100</span></div>')
    html = html.replace('<span id="runtimeSec" style="font-size:0.75rem;color:var(--text-3);margin-left:auto"></span>', f'<span id="runtimeSec" style="font-size:0.85rem;color:var(--text-2);margin-left:auto;">⏱ Thời gian xử lý: {menu.runtime_s:.2f}s | IDBO (Ngưỡng 0.28)</span>')

    # Script vẽ radar chart bằng Chart.js
    radar_script = f"""
    <script>
    document.addEventListener("DOMContentLoaded", () => {{
      const ctx = document.getElementById("nutrientRadar").getContext("2d");
      new Chart(ctx, {{
        type: "radar",
        data: {{
          labels: ["Năng lượng", "Protein", "Carbohydrate", "Chất béo", "Chất xơ", "Natri"],
          datasets: [
            {{
              label: "Mục tiêu chuẩn (100%)",
              data: [100, 100, 100, 100, 100, 100],
              borderColor: "rgba(217, 130, 43, 0.8)",
              borderWidth: 2,
              borderDash: [5, 5],
              backgroundColor: "rgba(217, 130, 43, 0.08)",
              pointRadius: 3
            }},
            {{
              label: "Thực đơn đề xuất (IDBO)",
              data: [{(totals['calories']/targets['calories'])*100:.1f}, {(totals['protein_g']/targets['protein_g'])*100:.1f}, {(totals['carbs_g']/targets['carbs_g'])*100:.1f}, {(totals['fat_g']/targets['fat_g'])*100:.1f}, {(totals['fiber_g']/targets['fiber_g'])*100:.1f}, {(totals['sodium_mg']/targets['sodium_mg'])*100:.1f}],
              borderColor: "rgba(45, 212, 191, 1)",
              borderWidth: 2.5,
              backgroundColor: "rgba(45, 212, 191, 0.25)",
              pointBackgroundColor: "#2dd4bf",
              pointRadius: 4
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          scales: {{
            r: {{
              angleLines: {{ color: "rgba(255,255,255,0.12)" }},
              grid: {{ color: "rgba(255,255,255,0.12)" }},
              suggestedMin: 0,
              suggestedMax: 130,
              ticks: {{ display: false }},
              pointLabels: {{ color: "#cbd5e1", font: {{ size: 11, weight: "bold" }} }}
            }}
          }},
          plugins: {{
            legend: {{ labels: {{ color: "#cbd5e1", font: {{ size: 10 }} }} }}
          }}
        }}
      }});
    }});
    </script>
    """
    html = html.replace('</body>', f'{radar_script}</body>')

    with open(DEMO_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[RENDERED] {DEMO_HTML}")

def take_screenshot():
    cmd = [
        "firefox",
        "-P", "headless",
        "--headless",
        "--screenshot", str(OUT_PNG),
        "--window-size", "1550,1100",
        "http://127.0.0.1:8000/demo_generated.html"
    ]
    print("[EXEC] " + " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[ERROR]", res.stderr)
    else:
        print(f"[SUCCESS] Screenshot saved: {OUT_PNG}")

if __name__ == "__main__":
    build_demo_page()
    take_screenshot()
