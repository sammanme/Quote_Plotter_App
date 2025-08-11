import React, { useState, useEffect } from 'react';
import ChartComponent from './components/ChartComponent';
import TableComponent from './components/TableComponents';
import './index.css';

function App() {
  const [brokerA, setBrokerA] = useState("");
  const [symbolA, setSymbolA] = useState("");
  const [brokerB, setBrokerB] = useState("");
  const [symbolB, setSymbolB] = useState("");
  const [timeRange, setTimeRange] = useState("all");
  const [spreadPoints, setSpreadPoints] = useState(10);

  const [brokerSymbols, setBrokerSymbols] = useState({}); // full mapping { broker: [symbols] }
  const [brokers, setBrokers] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/quotes/brokers&symbols") // your backend endpoint
      .then((res) => res.json())
      .then((data) => {
        // API should return: { brokers: { "Tradeview": ["BTCUSD", "ETHUSD"], "Zeal Capital": ["XAUUSD"] } }
        const symbolsData = data.brokers || {};
        setBrokerSymbols(symbolsData);
        setBrokers(Object.keys(symbolsData));
      })
      .catch((err) => console.error("Error fetching broker/symbol data:", err));
  }, []);

  // Reset symbols when broker changes
  useEffect(() => {
    setSymbolA("");
  }, [brokerA]);

  useEffect(() => {
    setSymbolB("");
  }, [brokerB]);


  return (
    <div style={{ padding: '20px' }}>
      <h1 className="animated-header">Quote Plotter</h1>
      {/* Broker A + Symbol A */}
      <div>
        <label>Broker A: </label>
        <select className="select-style"  value={brokerA} onChange={(e) => setBrokerA(e.target.value)}>
          <option value="">-- Select Broker A --</option>
          {brokers.map((b => (<option key={b} value={b}>{b}</option>)))}
        </select>
        <label>Symbol A: </label>
        <select className="select-style"  value={symbolA} onChange={(e) => setSymbolA(e.target.value)}>
          <option value="">-- Select Symbol --</option>
          {(brokerSymbols[brokerA] || []).map((s => <option key={s} value={s}>{s}</option>))}
        </select>
      </div>
      <div>
        <label>Broker B: </label>
        <select className="select-style"  value={brokerB} onChange={(e) => setBrokerB(e.target.value)}>
          <option value="">-- Select Broker B --</option>
          {brokers.map((b => (<option key={b} value={b}>{b}</option>)))}
        </select>
        <label>Symbol B: </label>
        <select className="select-style"  value={symbolB} onChange={(e) => setSymbolB(e.target.value)}>
          <option value="">-- Select Symbol --</option>
          {(brokerSymbols[brokerB] || []).map((s => <option key={s} value={s}>{s}</option>))}
        </select>
      </div>
      {/* Time Range & Spread Points */}
      <div>
        <label>Time Range: </label>
        <select className="select-style"  value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
          <option value="">-- Select Time Range --</option>
          <option value="all">All Data</option>
          <option value="1">Last 1 Hour</option>
          <option value="6">Last 6 Hours</option>
          <option value="24">Last 24 Hours</option>
        </select>
        <label>Spread Points: </label>
        <select className="select-style"  value={spreadPoints} onChange={(e) => setSpreadPoints(e.target.value)}>
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={30}>30</option>
          {[10, 20, 30].map((n => <option key={n} value={n}>{n}</option>))}
        </select>
      </div>
      <ChartComponent
        brokerA={brokerA} symbolA={symbolA}
        brokerB={brokerB} symbolB={symbolB}
        timeRange={timeRange} spreadPoints={spreadPoints}
      />
      <TableComponent
        brokerA={brokerA} symbolA={symbolA}
        brokerB={brokerB} symbolB={symbolB}
        timeRange={timeRange} spreadPoints={spreadPoints}
      />
    </div>
  );
}

export default App;