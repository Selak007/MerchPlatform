const express = require('express');
const cors = require('cors');
const db = require('./db');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 5000;
app.use(cors());
app.use(express.json());

// ─────────────────────────────────────────────────────────────
// UNIFIED DASHBOARD ENDPOINT — all 12 features in one call
// ─────────────────────────────────────────────────────────────
app.get('/api/merchant/:id/dashboard', async (req, res) => {
  const merchantId = req.params.id === 'all' ? null : parseInt(req.params.id);
  const whereMid = merchantId ? `WHERE a.merchant_id = ${merchantId}` : '';
  const andMid   = merchantId ? `AND a.merchant_id = ${merchantId}` : '';
  const midOnly  = merchantId ? `WHERE merchant_id = ${merchantId}` : '';

  try {
    // ─── 3.1 AI Business Health Score ────────────────────────
    const healthQ = await db.query(`
      WITH metrics AS (
        SELECT
          m.merchant_id,
          AVG(a.amount) avg_ticket,
          COUNT(a.auth_id) total_txns,
          COALESCE(SUM(CASE WHEN LOWER(a.auth_status) = 'approved' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*),0) * 100, 0) approval_rate,
          COALESCE(COUNT(f.fraud_id)::numeric / NULLIF(COUNT(a.auth_id),0) * 100, 0) fraud_rate
        FROM merchants m
        LEFT JOIN authorization_transactions a ON a.merchant_id = m.merchant_id
        LEFT JOIN fraud_events f ON f.auth_id = a.auth_id
        ${merchantId ? `WHERE m.merchant_id = ${merchantId}` : ''}
        GROUP BY m.merchant_id
      )
      SELECT
        merchant_id,
        ROUND(0.30 * approval_rate + 0.20 * (100 - fraud_rate) + 0.50 * 70, 2) AS health_score,
        ROUND(approval_rate, 2) AS approval_rate,
        ROUND(fraud_rate, 2) AS fraud_rate,
        CASE
          WHEN 0.30 * approval_rate + 0.20 * (100 - fraud_rate) + 0.50 * 70 >= 80 THEN 'Good'
          WHEN 0.30 * approval_rate + 0.20 * (100 - fraud_rate) + 0.50 * 70 >= 60 THEN 'Fair'
          ELSE 'Poor'
        END AS status
      FROM metrics
      ${merchantId ? '' : 'LIMIT 1'}
    `);

    // ─── 3.3 Peak Hours Heatmap ──────────────────────────────
    const peakQ = await db.query(`
      SELECT
        merchant_id,
        EXTRACT(HOUR FROM transaction_time)::int AS hour,
        COUNT(*)::int AS transaction_count,
        SUM(amount) AS total_volume
      FROM authorization_transactions
      ${midOnly}
      GROUP BY merchant_id, hour
      ORDER BY hour
    `);

    // ─── 3.4 Customer Type Breakdown ────────────────────────
    const customerQ = await db.query(`
      WITH customer_txns AS (
        SELECT card_number_masked, merchant_id, COUNT(*) txn_count, AVG(amount) avg_spend
        FROM authorization_transactions
        ${midOnly}
        GROUP BY card_number_masked, merchant_id
      ),
      p75 AS (
        SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_spend) AS p75_spend
        FROM customer_txns
      )
      SELECT
        merchant_id,
        SUM(CASE WHEN txn_count = 1 THEN 1 ELSE 0 END)::int AS one_time,
        SUM(CASE WHEN txn_count BETWEEN 2 AND 10 THEN 1 ELSE 0 END)::int AS regular,
        SUM(CASE WHEN avg_spend > (SELECT p75_spend FROM p75) THEN 1 ELSE 0 END)::int AS high_spender
      FROM customer_txns
      GROUP BY merchant_id
    `);

    // ─── 3.5 Fraud Risk Monitor ──────────────────────────────
    const fraudQ = await db.query(`
      SELECT
        a.merchant_id,
        f.fraud_type,
        COUNT(f.fraud_id)::int AS fraud_txns,
        COUNT(a.auth_id)::int AS total_txns,
        ROUND(COUNT(f.fraud_id)::numeric / NULLIF(COUNT(a.auth_id),0) * 100, 2) AS fraud_rate,
        AVG(f.risk_score) AS avg_risk_score
      FROM authorization_transactions a
      LEFT JOIN fraud_events f ON f.auth_id = a.auth_id
      ${midOnly}
      GROUP BY a.merchant_id, f.fraud_type
    `);

    // ─── 3.6 Competitor Benchmarking ─────────────────────────
    const benchQ = await db.query(`
      WITH industry_avg AS (
        SELECT mcc, AVG(amount) AS industry_ticket
        FROM authorization_transactions
        GROUP BY mcc
      )
      SELECT
        m.merchant_id,
        m.merchant_name,
        m.mcc,
        ROUND(AVG(a.amount)::numeric, 2) AS merchant_ticket,
        ROUND(i.industry_ticket::numeric, 2) AS industry_ticket,
        ROUND((AVG(a.amount) - i.industry_ticket)::numeric, 2) AS performance_gap
      FROM authorization_transactions a
      JOIN merchants m ON a.merchant_id = m.merchant_id
      JOIN industry_avg i ON i.mcc = m.mcc
      ${merchantId ? `WHERE m.merchant_id = ${merchantId}` : ''}
      GROUP BY m.merchant_id, m.merchant_name, m.mcc, i.industry_ticket
    `);

    // ─── 3.7 AI Pricing Advisor signal ───────────────────────
    const pricingQ = await db.query(`
      SELECT
        merchant_id,
        ROUND(AVG(amount)::numeric, 2) AS avg_ticket,
        ROUND(STDDEV(amount)::numeric, 2) AS price_variance
      FROM authorization_transactions
      ${midOnly}
      GROUP BY merchant_id
    `);

    // ─── 3.8 Transaction Health Monitor ─────────────────────
    const txnHealthQ = await db.query(`
      SELECT
        merchant_id,
        ROUND(SUM(CASE WHEN LOWER(auth_status) = 'approved' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*),0) * 100, 2) AS approval_rate,
        ROUND(SUM(CASE WHEN LOWER(auth_status) = 'declined' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*),0) * 100, 2) AS decline_rate
      FROM authorization_transactions
      ${midOnly}
      GROUP BY merchant_id
    `);

    // ─── 3.11 Repeat Customer Analysis ──────────────────────
    const repeatQ = await db.query(`
      WITH cust AS (
        SELECT merchant_id, card_number_masked, COUNT(*) txn_count
        FROM authorization_transactions
        ${midOnly}
        GROUP BY merchant_id, card_number_masked
      )
      SELECT
        merchant_id,
        ROUND(COUNT(*) FILTER (WHERE txn_count > 1)::numeric / NULLIF(COUNT(*),0) * 100, 2) AS repeat_rate,
        ROUND(COUNT(*) FILTER (WHERE txn_count = 1)::numeric / NULLIF(COUNT(*),0) * 100, 2) AS new_customer_rate,
        COUNT(DISTINCT card_number_masked)::int AS total_customers
      FROM cust
      GROUP BY merchant_id
    `);

    // ─── 3.12 Category / Product Insights ───────────────────
    const categoryQ = await db.query(`
      SELECT
        a.mcc,
        m.mcc_description AS category,
        SUM(a.amount) AS total_revenue,
        COUNT(*)::int AS txn_count,
        ROUND(AVG(a.amount)::numeric, 2) AS avg_ticket
      FROM authorization_transactions a
      LEFT JOIN merchants m ON m.mcc = a.mcc
      ${merchantId ? `WHERE a.merchant_id = ${merchantId}` : ''}
      GROUP BY a.mcc, m.mcc_description
      ORDER BY total_revenue DESC
      LIMIT 8
    `);

    // ─── 3.2 Smart Revenue Booster signals ──────────────────
    const health = healthQ.rows[0] || {};
    const repeat = repeatQ.rows[0] || {};
    const pricing = pricingQ.rows[0] || {};
    const txnHealth = txnHealthQ.rows[0] || {};
    const bench = benchQ.rows[0] || {};

    const recommendations = generateRecommendations({ health, repeat, pricing, txnHealth, bench });

    // ─── 3.9 Smart Alerts ────────────────────────────────────
    const alerts = generateAlerts({ health, txnHealth });

    // Assemble full response
    res.json({
      health_score: health,
      peak_hours: peakQ.rows,
      customer_segments: formatCustomerSegments(customerQ.rows[0]),
      fraud_monitor: fraudQ.rows,
      benchmarks: benchQ.rows[0] || null,
      pricing_signal: pricing,
      transaction_health: txnHealth,
      repeat_analysis: repeat,
      category_insights: categoryQ.rows,
      recommendations,
      alerts
    });

  } catch (err) {
    console.error(`[Dashboard Error] merchant_id=${merchantId}:`, err.message);
    res.status(500).json({ error: err.message });
  }
});

// ─── Helpers ──────────────────────────────────────────────────
function generateRecommendations({ health, repeat, pricing, txnHealth, bench }) {
  const recs = [];
  const avgTicket = parseFloat(pricing.avg_ticket || 0);
  const industryTicket = parseFloat(bench?.industry_ticket || 0);

  if (avgTicket > 0 && industryTicket > 0 && avgTicket < industryTicket) {
    recs.push({ type: 'Revenue Booster', priority: 'High', impact: Math.round((industryTicket - avgTicket) * 100),
      text: `Your avg ticket ($${avgTicket}) is $${(industryTicket - avgTicket).toFixed(2)} below industry ($${industryTicket}). Introduce combo offers to bridge the gap.` });
  }
  if (parseFloat(repeat.repeat_rate || 0) < 30) {
    recs.push({ type: 'Retention', priority: 'High', impact: 120,
      text: `Repeat rate is only ${repeat.repeat_rate || 0}%. Launch a loyalty reward program to convert one-time buyers.` });
  }
  if (parseFloat(txnHealth.approval_rate || 0) < 85) {
    recs.push({ type: 'Payment UX', priority: 'Medium', impact: 80,
      text: `Approval rate of ${txnHealth.approval_rate || 0}% is low. Enable payment retry flows and expand accepted card types.` });
  }
  if (recs.length === 0) {
    recs.push({ type: 'Revenue Booster', priority: 'Medium', impact: 60,
      text: 'Performance looks healthy. Consider seasonal promotional campaigns during peak hours for additional growth.' });
  }
  return recs;
}

function generateAlerts({ health, txnHealth }) {
  const alerts = [];
  if (parseFloat(health.fraud_rate || 0) > 3) {
    alerts.push({ title: 'Fraud Spike Detected', message: `Fraud rate at ${health.fraud_rate}% — above 3% threshold. Immediate review required.`, type: 'critical' });
  }
  if (parseFloat(txnHealth.decline_rate || 0) > 15) {
    alerts.push({ title: 'Decline Rate Surge', message: `Decline rate is ${txnHealth.decline_rate}%, significantly above normal levels.`, type: 'warning' });
  }
  if (alerts.length === 0) {
    alerts.push({ title: 'Systems Normal', message: 'All metrics within healthy thresholds. No active alerts.', type: 'info' });
  }
  return alerts;
}

function formatCustomerSegments(row) {
  if (!row) return [
    { segment: 'High Spenders', count: 0 },
    { segment: 'Regular', count: 0 },
    { segment: 'One-time', count: 0 }
  ];
  return [
    { segment: 'High Spenders', count: parseInt(row.high_spender) || 0, total_spend: 0 },
    { segment: 'Regular', count: parseInt(row.regular) || 0, total_spend: 0 },
    { segment: 'One-time', count: parseInt(row.one_time) || 0, total_spend: 0 }
  ];
}

// ─────────────────────────────────────────────────────────────
// SIMPLE ENDPOINTS (for individual widgets if needed)
// ─────────────────────────────────────────────────────────────
app.get('/api/health', (req, res) => res.json({ status: 'ok' }));

app.get('/api/merchants', async (req, res) => {
  try {
    const result = await db.query('SELECT merchant_id, merchant_name FROM merchants ORDER BY merchant_name');
    res.json(result.rows.length ? result.rows : [
      { merchant_id: 1, merchant_name: 'Acme Corp' },
      { merchant_id: 2, merchant_name: 'TechFlow Solutions' }
    ]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.listen(port, () => console.log(`Server running on port ${port}`));
