import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TableComponent = ({ brokerA, symbolA, brokerB, symbolB, timeRange, spreadPoints }) => {
  const [tableData, setTableData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log(`Fetching table data for brokerA=${brokerA}, symbolA=${symbolA}, brokerB=${brokerB}, symbolB=${symbolB}, timeRange=${timeRange}`);
        const response = await axios.get('http://localhost:8000/api/quotes/api/data', {
          params: { broker_a: brokerA, symbol_a: symbolA, broker_b: brokerB, symbol_b: symbolB, time_range_hours: timeRange },
        });
        const data = response.data.data;

        if (!data || data.length === 0) {
          console.warn('No data received for table');
          setTableData([]);
          return;
        }

        // Sort ascending by timestamp (oldest first)
        data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        // Determine min/max timestamp
        const minTimestamp = new Date(data[0].timestamp).getTime();
        const maxTimestamp = new Date(data[data.length - 1].timestamp).getTime();

        // Build common timestamp array with 1 second steps
        const commonTimestamps = [];
        for (let t = minTimestamp; t <= maxTimestamp; t += 1000) {
          commonTimestamps.push(new Date(t).toISOString());
        }

        // Group data by broker_symbol key
        const df = data.reduce((acc, row) => {
          const key = `${row.broker}_${row.symbol}`;
          if (!acc[key]) acc[key] = { timestamps: [], ask: [], bid: [] };
          acc[key].timestamps.push(row.timestamp);
          acc[key].ask.push(row.ask_price ?? null);
          acc[key].bid.push(row.bid_price ?? null);
          return acc;
        }, {});

        // Linear interpolation helper
        const linearInterpolate = (timestamps, values, newTimestamps) => {
          const result = [];
          let i = 0;
          for (let j = 0; j < newTimestamps.length; j++) {
            const t = new Date(newTimestamps[j]).getTime();
            while (i < timestamps.length - 1 && new Date(timestamps[i + 1]).getTime() < t) i++;
            if (i >= timestamps.length - 1) {
              result.push(values[values.length - 1] ?? null);
              continue;
            }
            const t0 = new Date(timestamps[i]).getTime();
            const t1 = new Date(timestamps[i + 1]).getTime();
            if (t === t0) {
              result.push(values[i]);
            } else if (t === t1) {
              result.push(values[i + 1]);
            } else {
              const v0 = values[i];
              const v1 = values[i + 1];
              if (v0 === null || v1 === null) {
                result.push(null);
              } else {
                result.push(v0 + ((v1 - v0) * (t - t0)) / (t1 - t0));
              }
            }
          }
          return result;
        };

        const keyA = `${brokerA}_${symbolA}`;
        const keyB = `${brokerB}_${symbolB}`;

        // Get interpolated ask/bid arrays on common timeline
        const askA = linearInterpolate(df[keyA]?.timestamps ?? [], df[keyA]?.ask ?? [], commonTimestamps);
        const bidA = linearInterpolate(df[keyA]?.timestamps ?? [], df[keyA]?.bid ?? [], commonTimestamps);
        const askB = linearInterpolate(df[keyB]?.timestamps ?? [], df[keyB]?.ask ?? [], commonTimestamps);
        const bidB = linearInterpolate(df[keyB]?.timestamps ?? [], df[keyB]?.bid ?? [], commonTimestamps);

        // Build table rows combining values per timestamp
        let combined = commonTimestamps.map((ts, i) => {
          const ask_a = askA[i];
          const bid_a = bidA[i];
          const ask_b = askB[i];
          const bid_b = bidB[i];

          // Calculate spread as ask_a - bid_b if both present
          const spread = (ask_a != null && bid_b != null) ? ask_a - bid_b : null;
          return {
            timestamp: new Date(ts).toLocaleString(),
            ask_a,
            bid_a,
            ask_b,
            bid_b,
            spread,
          };
        });

        // Sort descending (newest first) and slice to spreadPoints
        combined = combined.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, spreadPoints);

        // Format numbers to fixed (5) decimals or show 'N/A'
        const formatted = combined.map(row => ({
          timestamp: row.timestamp,
          ask_a: row.ask_a != null ? row.ask_a.toFixed(5) : 'N/A',
          bid_a: row.bid_a != null ? row.bid_a.toFixed(5) : 'N/A',
          ask_b: row.ask_b != null ? row.ask_b.toFixed(5) : 'N/A',
          bid_b: row.bid_b != null ? row.bid_b.toFixed(5) : 'N/A',
          spread: row.spread != null ? row.spread.toFixed(5) : 'N/A',
        }));

        setTableData(formatted);
      } catch (error) {
        console.error('Error fetching table data:', error);
      }
    };

    fetchData();
    const intervalId = setInterval(fetchData, 60000); // refreshes every 1 minute

    return () => clearInterval(intervalId);
  }, [brokerA, symbolA, brokerB, symbolB, timeRange, spreadPoints]);

  return (
    <table  className="table-style">
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>{`${brokerA} ${symbolA} Ask`}</th>
          <th>{`${brokerA} ${symbolA} Bid`}</th>
          <th>{`${brokerB} ${symbolB} Ask`}</th>
          <th>{`${brokerB} ${symbolB} Bid`}</th>
          <th>Spread (A-B)</th>
        </tr>
      </thead>
      <tbody>
        {tableData.length === 0 ? (
          <tr>
            <td colSpan={6} style={{ textAlign: 'center', padding: '8px'  }}>No data available</td>
          </tr>
        ) : (
          tableData.map((row, idx) => (
            <tr key={idx}>
              <td>{row.timestamp}</td>
              <td>{row.ask_a}</td>
              <td>{row.bid_a}</td>
              <td>{row.ask_b}</td>
              <td>{row.bid_b}</td>
              <td>{row.spread}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
};

export default TableComponent;
