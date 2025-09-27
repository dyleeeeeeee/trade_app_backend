"""
Advanced Profit & Loss Calculation Engine
Inspired by the Top 50 Economists from 1900 to the Present

This module implements sophisticated P&L calculations that incorporate:
- Keynesian counter-cyclical interventions
- Austrian market process and information theory (Hayek, Mises, Menger)
- Chicago School monetarism and free markets (Friedman, Becker)
- Behavioral economics biases (Kahneman, Thaler)
- Financial instability hypothesis (Minsky)
- Risk-adjusted returns and CAPM (Sharpe, Tobin)
- Black Swan theory and antifragility (Taleb)
- Creative destruction and entrepreneurship (Schumpeter, Kirzner)
- Transaction cost economics (Coase)
- Institutional economics (Ostrom, Commons, Veblen)
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class MarketRegime(Enum):
    KEYNESIAN_RECOVERY = "keynesian_recovery"  # Government stimulus needed
    HAYEKIAN_ORDER = "hayekian_order"  # Free market signals working
    FRIEDMAN_STAGFLATION = "friedman_stagflation"  # Monetary policy issues
    MINSKY_MOMENT = "minsky_moment"  # Financial instability
    TALEBS_BLACK_SWAN = "taleb_black_swan"  # Extreme uncertainty
    SCHUMPETER_CREATIVE_DESTRUCTION = "schumpeter_creative_destruction"  # Innovation disruption

class RiskProfile(Enum):
    KEYNESIAN_RISKY = "keynesian_risky"  # High risk, high reward
    HAYEKIAN_PRUDENT = "hayekian_prudent"  # Market discipline
    FRIEDMAN_MODERATE = "friedman_moderate"  # Balanced approach
    BECKER_OPTIMAL = "becker_optimal"  # Human capital focused

@dataclass
class TradeMetrics:
    """Multi-factor trade analysis inspired by top economists"""
    entry_price: float
    exit_price: float
    position_size: float
    holding_period: int  # hours
    volatility_at_entry: float
    market_regime: MarketRegime
    momentum_score: float  # Schumpeter/Kirzner innovation factor
    technical_score: float  # Marshall supply/demand signals
    fundamental_score: float  # Austrian subjective value
    behavioral_bias: float  # Kahneman prospect theory
    transaction_costs: float  # Coase transaction costs

@dataclass
class StrategyPerformance:
    """Comprehensive performance metrics from multiple economic schools"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float  # Sharpe modern portfolio theory
    sortino_ratio: float  # Downside risk focus
    max_drawdown: float
    calmar_ratio: float
    omega_ratio: float  # Shadwick & Keating beyond-Sharpe measure
    win_rate: float
    profit_factor: float
    expectancy: float  # Trade expectancy
    recovery_factor: float  # Minsky financial stability
    ulcer_index: float  # Behavioral risk measure
    tail_ratio: float  # Taleb black swan protection
    information_ratio: float  # Hayek information efficiency
    alpha: float  # Jensen alpha vs market
    beta: float  # Market sensitivity

class KeynesianInterventions:
    """
    John Maynard Keynes: Counter-cyclical policy interventions
    When markets fail, government must intervene to restore confidence and spending
    """

    @staticmethod
    def calculate_market_confidence_multiplier(market_regime: MarketRegime,
                                             economic_cycle_position: float) -> float:
        """
        Keynesian confidence multiplier during different market regimes
        """
        base_multiplier = 1.0

        regime_multipliers = {
            MarketRegime.KEYNESIAN_RECOVERY: 1.2,  # Government stimulus boost
            MarketRegime.HAYEKIAN_ORDER: 1.0,  # Natural market order
            MarketRegime.FRIEDMAN_STAGFLATION: 0.9,  # Monetary policy drag
            MarketRegime.MINSKY_MOMENT: 0.7,  # Financial panic discount
            MarketRegime.TALEBS_BLACK_SWAN: 0.5,  # Extreme uncertainty penalty
            MarketRegime.SCHUMPETER_CREATIVE_DESTRUCTION: 1.3  # Innovation premium
        }

        # Economic cycle adjustment (0-1 scale, 0=depression, 1=boom)
        cycle_adjustment = 1 + (economic_cycle_position - 0.5) * 0.4

        return regime_multipliers[market_regime] * cycle_adjustment

    @staticmethod
    def apply_fiscal_multiplier(economic_output: float, government_spending: float) -> float:
        """
        Keynesian fiscal multiplier effect
        """
        multiplier = 1 / (1 - 0.75)  # Simplified MPC = 0.75
        return economic_output + (government_spending * multiplier)

class HayekianInformationTheory:
    """
    F.A. Hayek: Knowledge is dispersed throughout society
    Markets coordinate this knowledge through price signals
    """

    @staticmethod
    def calculate_information_efficiency(price_changes: List[float],
                                       volume_changes: List[float]) -> float:
        """
        Hayekian information efficiency in price discovery
        """
        if len(price_changes) < 2:
            return 0.5

        # Price information content
        price_volatility = np.std(price_changes)
        price_mean = np.mean(price_changes)

        # Volume confirmation of price signals
        volume_correlation = np.corrcoef(price_changes, volume_changes)[0, 1] if len(volume_changes) == len(price_changes) else 0

        # Information efficiency score
        efficiency = 1 - (price_volatility / (abs(price_mean) + 1)) + (volume_correlation * 0.3)

        return max(0, min(1, efficiency))  # Bound between 0 and 1

    @staticmethod
    def assess_market_knowledge_dispersion(market_participants: int,
                                         information_flow: float) -> float:
        """
        How well is knowledge dispersed through the market?
        """
        # More participants generally means better knowledge dispersion
        participant_factor = min(1, market_participants / 1000)

        # Information flow efficiency
        flow_factor = min(1, information_flow)

        return (participant_factor + flow_factor) / 2

class FriedmanMonetaristFramework:
    """
    Milton Friedman: Control money supply to control inflation
    Long-run monetary neutrality, short-run Phillips curve trade-offs
    """

    @staticmethod
    def calculate_monetary_neutrality_adjustment(money_supply_growth: float,
                                               inflation_expectations: float) -> float:
        """
        Friedman's long-run monetary neutrality
        """
        # In long run, money supply changes affect prices, not real output
        neutrality_factor = 1 + (money_supply_growth - inflation_expectations) * 0.1
        return max(0.8, min(1.2, neutrality_factor))

    @staticmethod
    def assess_phillips_curve_tradeoff(unemployment_rate: float,
                                     inflation_rate: float) -> float:
        """
        Short-run Phillips curve relationship
        """
        # Natural rate of unemployment (Friedman)
        natural_rate = 0.05  # 5%

        # Deviation from natural rate affects inflation expectations
        deviation = unemployment_rate - natural_rate

        # Phillips curve: lower unemployment = higher inflation
        expected_tradeoff = -deviation * 2  # Simplified relationship

        return inflation_rate - expected_tradeoff

class KahnemanBehavioralEconomics:
    """
    Daniel Kahneman: Humans are predictably irrational
    Prospect theory, cognitive biases, loss aversion
    """

    @staticmethod
    def calculate_loss_aversion_impact(gains: float, losses: float) -> float:
        """
        Prospect theory: losses hurt more than gains help
        Loss aversion coefficient ≈ 2.25
        """
        if losses == 0:
            return 1.0

        loss_aversion_coefficient = 2.25
        behavioral_impact = (gains * 1) + (losses * loss_aversion_coefficient)

        # Convert to multiplier
        return 1 + (behavioral_impact / (abs(gains) + abs(losses) + 1)) * 0.2

    @staticmethod
    def apply_anchoring_bias_correction(anchor_price: float,
                                      market_price: float) -> float:
        """
        Anchoring bias: initial prices influence perceptions
        """
        if anchor_price == 0:
            return 1.0

        bias_factor = market_price / anchor_price
        correction = 1 + (bias_factor - 1) * 0.1  # Dampened correction

        return max(0.9, min(1.1, correction))

class MinskyFinancialInstability:
    """
    Hyman Minsky: Stability leads to instability
    Financial crises are endogenous to capitalist economies
    """

    @staticmethod
    def calculate_financial_fragility_index(debt_to_equity: float,
                                          interest_coverage: float,
                                          cash_flow_volatility: float) -> float:
        """
        Minsky's financial fragility assessment
        """
        # High debt, low coverage, high volatility = fragile
        fragility_score = (debt_to_equity * 0.4) + ((1/interest_coverage) * 0.3) + (cash_flow_volatility * 0.3)

        # Convert to stability multiplier
        stability_multiplier = 1 / (1 + fragility_score)

        return max(0.3, stability_multiplier)

    @staticmethod
    def predict_minsky_moment_probability(euphoria_index: float,
                                        leverage_ratio: float) -> float:
        """
        Probability of hitting a Minsky moment
        """
        # Euphoria + leverage = crisis probability
        crisis_probability = (euphoria_index * 0.6) + (leverage_ratio * 0.4)

        return min(1.0, crisis_probability)

class TalebBlackSwanTheory:
    """
    Nassim Taleb: Black swans drive history, not normal distributions
    Focus on tail risk and antifragility
    """

    @staticmethod
    def calculate_tail_risk_exposure(returns: List[float]) -> float:
        """
        Extreme tail risk assessment
        """
        if len(returns) < 10:
            return 0.5

        # 5% tail risk (VaR-like measure)
        sorted_returns = sorted(returns)
        tail_index = int(len(returns) * 0.05)
        fifth_percentile = sorted_returns[tail_index]

        # 95% confidence VaR
        tail_risk = abs(fifth_percentile)

        return tail_risk

    @staticmethod
    def measure_antifragility(exposure_to_volatility: float,
                             performance_under_stress: float) -> float:
        """
        Taleb's antifragility: benefit from volatility
        """
        # Antifragility = performance improvement under stress
        antifragility_score = performance_under_stress / (exposure_to_volatility + 1)

        return max(0, antifragility_score)

class SchumpeterCreativeDestruction:
    """
    Joseph Schumpeter: Capitalism progresses through creative destruction
    Innovation and entrepreneurship drive economic growth
    """

    @staticmethod
    def calculate_innovation_premium(innovation_index: float,
                                   disruption_potential: float) -> float:
        """
        Premium for innovative, disruptive strategies
        """
        innovation_multiplier = 1 + (innovation_index * 0.3) + (disruption_potential * 0.2)

        return min(2.0, innovation_multiplier)

    @staticmethod
    def assess_entrepreneurial_value_creation(kirzner_opportunities: int,
                                            schumpeter_innovations: int) -> float:
        """
        Value creation through entrepreneurship
        Kirzner: market arbitrage opportunities
        Schumpeter: radical innovations
        """
        arbitrage_value = kirzner_opportunities * 0.1
        innovation_value = schumpeter_innovations * 0.3

        total_value_creation = arbitrage_value + innovation_value

        return 1 + total_value_creation

class BeckerHumanCapital:
    """
    Gary Becker: Investments in human capital drive productivity
    Education, skills, health as economic assets
    """

    @staticmethod
    def calculate_human_capital_roi(education_years: float,
                                  experience_years: float,
                                  skill_development: float) -> float:
        """
        ROI from human capital investments
        """
        education_roi = education_years * 0.08  # 8% annual return per year education
        experience_roi = experience_years * 0.03  # 3% annual return per year experience
        skill_roi = skill_development * 0.05

        total_roi = education_roi + experience_roi + skill_roi

        return 1 + total_roi

    @staticmethod
    def assess_discrimination_penalty(discrimination_factor: float) -> float:
        """
        Becker's economics of discrimination
        """
        # Discrimination reduces market efficiency
        efficiency_penalty = discrimination_factor * 0.2

        return 1 - efficiency_penalty

class CoaseTransactionCosts:
    """
    Ronald Coase: Transaction costs determine economic organization
    Firms exist to minimize transaction costs
    """

    @staticmethod
    def calculate_transaction_cost_efficiency(search_costs: float,
                                           bargaining_costs: float,
                                           enforcement_costs: float) -> float:
        """
        Transaction cost efficiency multiplier
        """
        total_transaction_costs = search_costs + bargaining_costs + enforcement_costs

        # Lower transaction costs = higher efficiency
        efficiency_multiplier = 1 / (1 + total_transaction_costs)

        return max(0.5, efficiency_multiplier)

    @staticmethod
    def assess_firm_vs_market_boundary(transaction_frequency: float,
                                     asset_specificity: float) -> str:
        """
        Coase's theory: when to use firms vs markets
        """
        # High frequency + high specificity = use firms
        boundary_score = (transaction_frequency * 0.6) + (asset_specificity * 0.4)

        if boundary_score > 0.7:
            return "firm"
        elif boundary_score < 0.3:
            return "market"
        else:
            return "hybrid"

class AdvancedEconomicCalculator:
    """
    Master calculator integrating insights from top economists
    """

    def __init__(self):
        self.keynes = KeynesianInterventions()
        self.hayek = HayekianInformationTheory()
        self.friedman = FriedmanMonetaristFramework()
        self.kahneman = KahnemanBehavioralEconomics()
        self.minsky = MinskyFinancialInstability()
        self.taleb = TalebBlackSwanTheory()
        self.schumpeter = SchumpeterCreativeDestruction()
        self.becker = BeckerHumanCapital()
        self.coase = CoaseTransactionCosts()

    def calculate_comprehensive_pnl(self, trade_metrics: TradeMetrics,
                                   market_data: Dict,
                                   economic_context: Dict) -> Dict[str, float]:
        """
        Multi-factor P&L calculation inspired by 50 top economists
        """
        # Base P&L calculation
        basic_pnl = (trade_metrics.exit_price - trade_metrics.entry_price) * trade_metrics.position_size

        # Keynesian interventions
        keynesian_multiplier = self.keynes.calculate_market_confidence_multiplier(
            trade_metrics.market_regime,
            economic_context.get('economic_cycle_position', 0.5)
        )

        # Hayekian information efficiency
        information_efficiency = self.hayek.calculate_information_efficiency(
            market_data.get('price_changes', []),
            market_data.get('volume_changes', [])
        )

        # Friedman monetary neutrality
        monetary_adjustment = self.friedman.calculate_monetary_neutrality_adjustment(
            economic_context.get('money_supply_growth', 0.02),
            economic_context.get('inflation_expectations', 0.02)
        )

        # Kahneman behavioral biases
        behavioral_impact = self.kahneman.calculate_loss_aversion_impact(
            max(0, basic_pnl), max(0, -basic_pnl)
        )

        # Minsky financial stability
        financial_fragility = self.minsky.calculate_financial_fragility_index(
            economic_context.get('debt_to_equity', 1.0),
            economic_context.get('interest_coverage', 5.0),
            economic_context.get('cash_flow_volatility', 0.1)
        )

        # Taleb tail risk
        tail_risk = self.taleb.calculate_tail_risk_exposure(
            market_data.get('historical_returns', [])
        )

        # Schumpeter innovation premium
        innovation_premium = self.schumpeter.calculate_innovation_premium(
            trade_metrics.momentum_score,
            trade_metrics.technical_score
        )

        # Becker human capital
        human_capital_roi = self.becker.calculate_human_capital_roi(
            economic_context.get('education_years', 16),
            economic_context.get('experience_years', 5),
            trade_metrics.fundamental_score
        )

        # Coase transaction costs
        transaction_efficiency = self.coase.calculate_transaction_cost_efficiency(
            trade_metrics.transaction_costs,
            trade_metrics.transaction_costs * 0.5,
            trade_metrics.transaction_costs * 0.3
        )

        # Composite multiplier
        composite_multiplier = (
            keynesian_multiplier * 0.15 +
            information_efficiency * 0.15 +
            monetary_adjustment * 0.1 +
            behavioral_impact * 0.1 +
            financial_fragility * 0.15 +
            (1 / (1 + tail_risk)) * 0.1 +  # Inverse tail risk
            innovation_premium * 0.1 +
            human_capital_roi * 0.05 +
            transaction_efficiency * 0.1
        )

        # Final P&L calculation
        adjusted_pnl = basic_pnl * composite_multiplier

        # Holding period adjustment (time value of money)
        time_decay = math.exp(-trade_metrics.holding_period * 0.001)
        final_pnl = adjusted_pnl * time_decay

        return {
            'basic_pnl': basic_pnl,
            'final_pnl': final_pnl,
            'keynesian_multiplier': keynesian_multiplier,
            'information_efficiency': information_efficiency,
            'monetary_adjustment': monetary_adjustment,
            'behavioral_impact': behavioral_impact,
            'financial_fragility': financial_fragility,
            'tail_risk': tail_risk,
            'innovation_premium': innovation_premium,
            'human_capital_roi': human_capital_roi,
            'transaction_efficiency': transaction_efficiency,
            'composite_multiplier': composite_multiplier,
            'time_decay': time_decay
        }

    def calculate_strategy_performance_economics(self, returns: List[float],
                                               invested_amount: float,
                                               economic_context: Dict) -> StrategyPerformance:
        """
        Strategy performance using insights from top economists
        """
        if not returns:
            return StrategyPerformance(*[0] * 20)

        # Basic metrics
        total_return = sum(returns)
        annualized_return = total_return * (365 / max(1, economic_context.get('time_period_days', 365)))

        # Volatility with Taleb black swan considerations
        volatility = math.sqrt(sum((r - total_return/len(returns))**2 for r in returns) / len(returns))
        tail_risk = self.taleb.calculate_tail_risk_exposure(returns)

        # Sharpe ratio (Sharpe)
        risk_free_rate = economic_context.get('risk_free_rate', 0.02)
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0

        # Sortino ratio (focus on downside volatility)
        downside_returns = [r for r in returns if r < risk_free_rate]
        downside_deviation = math.sqrt(sum(r**2 for r in downside_returns) / len(downside_returns)) if downside_returns else 0
        sortino_ratio = (annualized_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0

        # Maximum drawdown
        cumulative = [1]
        max_dd = 0
        peak = 1

        for r in returns:
            cumulative_val = cumulative[-1] * (1 + r)
            cumulative.append(cumulative_val)

            if cumulative_val > peak:
                peak = cumulative_val

            dd = (peak - cumulative_val) / peak
            max_dd = max(max_dd, dd)

        calmar_ratio = annualized_return / max_dd if max_dd > 0 else 0

        # Omega ratio (Shadwick & Keating)
        upside_returns = [r for r in returns if r > 0]
        downside_sum = abs(sum(downside_returns)) if downside_returns else 0
        upside_sum = sum(upside_returns) if upside_returns else 0
        omega_ratio = upside_sum / downside_sum if downside_sum > 0 else float('inf')

        # Win rate and profit factor
        win_rate = len([r for r in returns if r > 0]) / len(returns) * 100
        gross_profit = sum(r for r in returns if r > 0)
        gross_loss = abs(sum(r for r in returns if r < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Expectancy (Kahneman behavioral considerations)
        avg_win = gross_profit / len(upside_returns) if upside_returns else 0
        avg_loss = gross_loss / len(downside_returns) if downside_returns else 0
        expectancy = (avg_win * win_rate/100) - (avg_loss * (100-win_rate)/100)

        # Recovery factor (Minsky)
        recovery_factor = total_return / max_dd if max_dd > 0 else 0

        # Ulcer index (behavioral risk measure)
        ulcer_index = math.sqrt(sum(dd**2 for dd in [max_dd] * len(returns)) / len(returns))

        # Tail ratio (Taleb)
        sorted_returns = sorted(returns)
        if len(sorted_returns) >= 20:
            percentile_95 = sorted_returns[int(len(sorted_returns) * 0.95)]
            percentile_5 = sorted_returns[int(len(sorted_returns) * 0.05)]
            tail_ratio = percentile_95 / abs(percentile_5) if percentile_5 != 0 else 0
        else:
            tail_ratio = 1.0

        # Information ratio (Hayek)
        benchmark_return = economic_context.get('benchmark_return', annualized_return * 0.8)
        tracking_error = volatility * 0.8  # Simplified
        information_ratio = (annualized_return - benchmark_return) / tracking_error if tracking_error > 0 else 0

        # Alpha and Beta (CAPM, Sharpe)
        beta = economic_context.get('market_beta', 1.0)
        market_return = economic_context.get('market_return', annualized_return * 0.9)
        alpha = annualized_return - (risk_free_rate + beta * (market_return - risk_free_rate))

        return StrategyPerformance(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_dd,
            calmar_ratio=calmar_ratio,
            omega_ratio=omega_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            expectancy=expectancy,
            recovery_factor=recovery_factor,
            ulcer_index=ulcer_index,
            tail_ratio=tail_ratio,
            information_ratio=information_ratio,
            alpha=alpha,
            beta=beta
        )

# Global instance for use across the application
economic_calculator = AdvancedEconomicCalculator()
