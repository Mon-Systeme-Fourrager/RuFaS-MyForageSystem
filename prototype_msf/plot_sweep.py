import matplotlib.pyplot as plt
import numpy as np

delays = [0, 1, 2, 3, 4]
runoff = [0.5862, 0.3266, 0.3668, 0.4051, 0.3986]
n_avail = [60.249, 61.247, 61.407, 60.457, 60.46]
root_n = [32.927, 33.800, 33.840, 38.795, 35.72]

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle('MSF Expert System — Prototype 1\nManure application timing sweep (dairy slurry, 30 t/ha, Quebec 2013)',
             fontsize=13, fontweight='bold')

# Plot 1 — Runoff
axes[0].plot(delays, runoff, 'o-', color='#DC2626', linewidth=2, markersize=8)
axes[0].axvline(x=1, color='#DC2626', linestyle='--', alpha=0.5, label='Optimum: delay 1')
axes[0].set_title('Nitrate Runoff (35 days)', fontweight='bold')
axes[0].set_xlabel('Days of delay')
axes[0].set_ylabel('Total runoff (kg N)')
axes[0].legend()
axes[0].set_xticks(delays)
axes[0].grid(True, alpha=0.3)

# Plot 2 — N available
axes[1].plot(delays, n_avail, 'o-', color='#1E40AF', linewidth=2, markersize=8)
axes[1].axvline(x=2, color='#1E40AF', linestyle='--', alpha=0.5, label='Optimum: delay 2')
axes[1].set_title('Plant-Available N at Day 30', fontweight='bold')
axes[1].set_xlabel('Days of delay')
axes[1].set_ylabel('Available N (kg)')
axes[1].legend()
axes[1].set_xticks(delays)
axes[1].grid(True, alpha=0.3)

# Plot 3 — Root zone N
axes[2].plot(delays, root_n, 'o-', color='#2D6A4F', linewidth=2, markersize=8)
axes[2].axvline(x=3, color='#2D6A4F', linestyle='--', alpha=0.5, label='Optimum: delay 3')
axes[2].set_title('Root Zone N at Day 30 (Layer 1)', fontweight='bold')
axes[2].set_xlabel('Days of delay')
axes[2].set_ylabel('Root zone N (kg)')
axes[2].legend()
axes[2].set_xticks(delays)
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('prototype_msf/sweep_results_plot.png', dpi=150, bbox_inches='tight')
print('Plot saved to prototype_msf/sweep_results_plot.png')
plt.show()
