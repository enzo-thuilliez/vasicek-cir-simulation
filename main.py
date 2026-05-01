import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

# Create assets directory if it doesn't exist
os.makedirs("assets", exist_ok=True)

class ShortRateModel:
    """Base class for short rate models."""
    def __init__(self, r0, kappa, theta, sigma, T, dt):
        self.r0 = r0          # Initial interest rate
        self.kappa = kappa    # Speed of mean reversion
        self.theta = theta    # Long-term mean level
        self.sigma = sigma    # Volatility parameter
        self.T = T            # Time horizon in years
        self.dt = dt          # Time step (e.g., 1/252 for daily)
        self.n_steps = int(T / dt)
        self.t = np.linspace(0, T, self.n_steps)

class Vasicek(ShortRateModel):
    def simulate(self):
        rates = np.zeros(self.n_steps)
        rates[0] = self.r0
        for i in range(1, self.n_steps):
            # Formula: dr = kappa * (theta - r) * dt + sigma * dW
            dr = self.kappa * (self.theta - rates[i-1]) * self.dt + \
                 self.sigma * np.sqrt(self.dt) * np.random.normal()
            rates[i] = rates[i-1] + dr
        return rates

class CIR(ShortRateModel):
    def simulate(self):
        rates = np.zeros(self.n_steps)
        rates[0] = self.r0
        for i in range(1, self.n_steps):
            # Formula: dr = kappa * (theta - r) * dt + sigma * sqrt(r) * dW
            # We use max(rates[i-1], 0) to prevent numerical errors with sqrt
            prev_r = max(rates[i-1], 0)
            dr = self.kappa * (self.theta - prev_r) * self.dt + \
                 self.sigma * np.sqrt(prev_r) * np.sqrt(self.dt) * np.random.normal()
            rates[i] = prev_r + dr
        return rates

def plot_comparison(params, n_paths=5, seed=42):
    """
    Figure 1 — Vasicek vs CIR: multi-path comparison.
    Saved to assets/vasicek_vs_cir.png
    """
    np.random.seed(seed)
    v_model = Vasicek(**params)
    c_model = CIR(**params)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    fig.suptitle("Short Rate Models: Vasicek vs CIR", fontsize=14, fontweight="bold")

    for i in range(n_paths):
        v_path = v_model.simulate()
        c_path = c_model.simulate()
        axes[0].plot(v_model.t, v_path * 100, color="crimson", alpha=0.5,
                     label="Vasicek paths" if i == 0 else "")
        axes[1].plot(c_model.t, c_path * 100, color="steelblue", alpha=0.5,
                     label="CIR paths" if i == 0 else "")

    for ax, title in zip(axes, ["Vasicek Model", "CIR Model"]):
        ax.axhline(y=params["theta"] * 100, color="black", linestyle="--",
                   linewidth=1, label=f"Long-run mean θ = {params['theta']*100:.0f}%")
        ax.axhline(y=0, color="gray", linestyle=":", linewidth=1, label="Zero lower bound")
        ax.set_title(title, fontsize=12)
        ax.set_xlabel("Time (Years)")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Interest Rate")
    plt.tight_layout()
    plt.savefig("assets/vasicek_vs_cir.png", dpi=150, bbox_inches="tight")
    print("Saved: assets/vasicek_vs_cir.png")
    plt.show()

def plot_feller_condition(params_ok, params_violated, n_paths=5, seed=42):
    """
    Figure 2 — CIR: Feller condition satisfied vs violated.
    Saved to assets/cir_feller_condition.png
    """
    np.random.seed(seed)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    fig.suptitle("CIR Model — Feller Condition: Satisfied vs Violated",
                 fontsize=14, fontweight="bold")

    for p, ax, label, color in zip(
        [params_ok, params_violated],
        axes,
        ["Feller satisfied  (2κθ > σ²)", "Feller violated  (2κθ ≤ σ²)"],
        ["steelblue", "darkorange"]
    ):
        model = CIR(**p)
        feller_val = 2 * p["kappa"] * p["theta"]
        sigma2 = p["sigma"] ** 2
        subtitle = f"2κθ = {feller_val:.3f},  σ² = {sigma2:.3f}"

        for i in range(n_paths):
            path = model.simulate()
            ax.plot(model.t, path * 100, color=color, alpha=0.5,
                    label="CIR paths" if i == 0 else "")

        ax.axhline(y=0, color="gray", linestyle=":", linewidth=1, label="Zero lower bound")
        ax.axhline(y=p["theta"] * 100, color="black", linestyle="--",
                   linewidth=1, label=f"θ = {p['theta']*100:.0f}%")
        ax.set_title(f"{label}\n{subtitle}", fontsize=11)
        ax.set_xlabel("Time (Years)")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Interest Rate")
    plt.tight_layout()
    plt.savefig("assets/cir_feller_condition.png", dpi=150, bbox_inches="tight")
    print("Saved: assets/cir_feller_condition.png")
    plt.show()

def main():
    # --- Parameters: Feller condition satisfied ---
    params = {
        "r0": 0.01,    # 1% initial rate
        "kappa": 2.0,  # Strong mean reversion
        "theta": 0.02, # 2% long-run mean
        "sigma": 0.1,  # Volatility
        "T": 1.0,      # 1-year horizon
        "dt": 1/252    # Daily steps
    }

    # --- Parameters: Feller condition violated (high sigma) ---
    params_feller_violated = {**params, "sigma": 0.35}

    # Check Feller condition
    feller_ok = 2 * params["kappa"] * params["theta"] > params["sigma"] ** 2
    feller_violated = 2 * params_feller_violated["kappa"] * params_feller_violated["theta"] > params_feller_violated["sigma"] ** 2
    print(f"Feller condition satisfied (base params):     {feller_ok}")
    print(f"Feller condition satisfied (high sigma):      {feller_violated}")

    # Generate and save figures
    plot_comparison(params, n_paths=5)
    plot_feller_condition(params, params_feller_violated, n_paths=5)

if __name__ == "__main__":
    main()
