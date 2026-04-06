import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api } from '../services/api';
import { formatCurrency, formatEnergy } from '../utils/formatters';

function Billing() {
  const [currentMonth, setCurrentMonth] = useState(null);
  const [history, setHistory] = useState([]);
  const [slabRates, setSlabRates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadBillingData();
  }, []);

  const loadBillingData = async () => {
    try {
      setLoading(true);
      const [current, hist, slabs] = await Promise.all([
        api.getCurrentMonthBill(),
        api.getMonthlyComparison(6),
        api.getSlabRates()
      ]);
      setCurrentMonth(current);
      // FIX: Extract months array from response
      setHistory(hist.months || []);
      // FIX: Extract slab_rates array from response
      setSlabRates(slabs.slab_rates || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <h1>Billing & Analysis</h1>
        <p>Loading billing data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <h1>Billing & Analysis</h1>
        <div style={styles.errorBox}>Error loading billing data: {error}</div>
      </div>
    );
  }

  // FIX: Calculate days in period from billing_period_start/end
  const getDaysInPeriod = () => {
    if (!currentMonth) return 0;
    const start = new Date(currentMonth.billing_period_start);
    const end = new Date(currentMonth.billing_period_end);
    const now = new Date();
    const effectiveEnd = now < end ? now : end;
    return Math.ceil((effectiveEnd - start) / (1000 * 60 * 60 * 24)) + 1;
  };

  const daysInPeriod = getDaysInPeriod();

  return (
    <div style={styles.container}>
      <h1>Billing & Analysis</h1>

      {/* Current Month Summary */}
      {currentMonth && (
        <div style={styles.currentMonthCard}>
          <h2>Current Month: {currentMonth.billing_period_start?.substring(0, 7)}</h2>
          <div style={styles.summaryGrid}>
            <div style={styles.summaryItem}>
              <div style={styles.summaryLabel}>Total Consumption</div>
              <div style={styles.summaryValue}>{formatEnergy(currentMonth.total_kwh)}</div>
            </div>
            <div style={styles.summaryItem}>
              <div style={styles.summaryLabel}>Estimated Bill</div>
              <div style={{...styles.summaryValue, color: '#e74c3c'}}>{formatCurrency(currentMonth.total_cost_inr)}</div>
            </div>
            <div style={styles.summaryItem}>
              <div style={styles.summaryLabel}>Days Elapsed</div>
              <div style={styles.summaryValue}>{daysInPeriod}</div>
            </div>
            <div style={styles.summaryItem}>
              <div style={styles.summaryLabel}>Avg Daily Cost</div>
              <div style={styles.summaryValue}>
                {daysInPeriod > 0 ? formatCurrency(currentMonth.total_cost_inr / daysInPeriod) : 'N/A'}
              </div>
            </div>
          </div>

          {/* Slab Breakdown */}
          {currentMonth.slab_breakdown && currentMonth.slab_breakdown.length > 0 && (
            <div style={styles.slabBreakdown}>
              <h3>Usage by Slab</h3>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Slab</th>
                    <th style={styles.th}>Units (kWh)</th>
                    <th style={styles.th}>Rate</th>
                    <th style={styles.th}>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {currentMonth.slab_breakdown.map((slab, idx) => (
                    <tr key={idx}>
                      <td style={styles.td}>{slab.slab}</td>
                      <td style={styles.td}>{slab.units?.toFixed(2)}</td>
                      <td style={styles.td}>{formatCurrency(slab.rate)}/kWh</td>
                      <td style={styles.td}>{formatCurrency(slab.cost)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* 6-Month History Chart */}
      {history && history.length > 0 && (
        <div style={styles.chartCard}>
          <h2>6-Month Billing History</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis yAxisId="left" orientation="left" stroke="#3498db" />
              <YAxis yAxisId="right" orientation="right" stroke="#e74c3c" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="total_kwh" fill="#3498db" name="Energy (kWh)" />
              <Bar yAxisId="right" dataKey="total_cost_inr" fill="#e74c3c" name="Cost (₹)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Slab Rates Table */}
      {slabRates && slabRates.length > 0 && (
        <div style={styles.slabRatesCard}>
          <h2>Current Slab Rates</h2>
          <p style={styles.note}>These are the configured electricity tariff slabs for billing.</p>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Slab Range</th>
                <th style={styles.th}>Rate per Unit</th>
              </tr>
            </thead>
            <tbody>
              {slabRates.map((slab, idx) => (
                <tr key={idx}>
                  <td style={styles.td}>{slab.slab_label}</td>
                  <td style={styles.td}>{formatCurrency(slab.rate_per_unit)}/kWh</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    padding: '20px',
    maxWidth: '1200px',
    margin: '0 auto'
  },
  currentMonthCard: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  summaryGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '15px',
    marginTop: '15px'
  },
  summaryItem: {
    textAlign: 'center'
  },
  summaryLabel: {
    fontSize: '14px',
    color: '#7f8c8d',
    marginBottom: '5px'
  },
  summaryValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#2c3e50'
  },
  slabBreakdown: {
    marginTop: '25px'
  },
  chartCard: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  slabRatesCard: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  note: {
    fontSize: '14px',
    color: '#7f8c8d',
    marginBottom: '15px'
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: '10px'
  },
  th: {
    backgroundColor: '#ecf0f1',
    padding: '10px',
    textAlign: 'left',
    borderBottom: '2px solid #bdc3c7'
  },
  td: {
    padding: '10px',
    borderBottom: '1px solid #ecf0f1'
  },
  errorBox: {
    backgroundColor: '#fee',
    color: '#c33',
    padding: '15px',
    borderRadius: '4px',
    marginTop: '10px'
  }
};

export default Billing;
