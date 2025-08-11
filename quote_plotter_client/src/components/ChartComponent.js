import React, { useState, useEffect, useRef, useMemo} from 'react';
import { Line } from 'react-chartjs-2';
import zoomPlugin from 'chartjs-plugin-zoom';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  TimeScale,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import '../index.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, TimeScale, Title, Tooltip, Legend, zoomPlugin);

const ChartComponent = ({ brokerA, symbolA, brokerB, symbolB, timeRange, spreadPoints }) => {
  const [chartData, setChartData] = useState(null);
  const [view, setView] = useState('ask_bid');
  const chartRef = useRef(null);
  const zoomRangeRef = useRef(null);

  // Make zoomKey stable so it doesn't trigger useEffect unnecessarily
  const zoomKey = useMemo(
    () => `${brokerA}_${symbolA}_${brokerB}_${symbolB}_zoom`,
    [brokerA, symbolA, brokerB, symbolB]
  );


  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log(`Fetching data for brokerA=${brokerA}, symbolA=${symbolA}, brokerB=${brokerB}, symbolB=${symbolB}, timeRange=${timeRange}`);
        const response = await axios.get('http://localhost:8000/api/quotes/api/data', {
          params: { broker_a: brokerA, symbol_a: symbolA, broker_b: brokerB, symbol_b: symbolB, time_range_hours: timeRange },
        });
        const data = response.data.data;

        if (!data || data.length === 0) {
          console.warn('No data received from API');
          setChartData({ labels: [], datasets: [] });
          return;
        }

        // Sort data by timestamp
        data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        // Get min and max timestamps
        const minTimestamp = new Date(data[0].timestamp).getTime();
        const maxTimestamp = new Date(data[data.length - 1].timestamp).getTime();

        // Create common timestamp index with 1-second frequency
        const commonTimestamps = [];
        for (let t = minTimestamp; t <= maxTimestamp; t += 1000) {
          commonTimestamps.push(new Date(t).toISOString());
        }

        const df = data.reduce((acc, row) => {
          const key = `${row.broker}_${row.symbol}`;
          if (!acc[key]) acc[key] = { timestamps: [], ask: [], bid: [] };
          acc[key].timestamps.push(row.timestamp);
          acc[key].ask.push(row.ask_price || null);
          acc[key].bid.push(row.bid_price || null);
          return acc;
        }, {});

        // Linear interpolation function
        const linearInterpolate = (timestamps, values, newTimestamps) => {
          const result = [];
          let i = 0;
          for (let j = 0; j < newTimestamps.length; j++) {
            const t = new Date(newTimestamps[j]).getTime();
            while (i < timestamps.length - 1 && new Date(timestamps[i + 1]).getTime() < t) i++;
            if (i >= timestamps.length - 1) {
              result.push(values[values.length - 1] || null);
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
                result.push(v0 + (v1 - v0) * (t - t0) / (t1 - t0));
              }
            }
          }
          return result;
        };

        const keyA = `${brokerA}_${symbolA}`;
        const keyB = `${brokerB}_${symbolB}`;

        const timestampsA = df[keyA]?.timestamps || [];
        const timestampsB = df[keyB]?.timestamps || [];

        const askA = linearInterpolate(timestampsA, df[keyA]?.ask || [], commonTimestamps);
        const bidA = linearInterpolate(timestampsA, df[keyA]?.bid || [], commonTimestamps);
        const askB = linearInterpolate(timestampsB, df[keyB]?.ask || [], commonTimestamps);
        const bidB = linearInterpolate(timestampsB, df[keyB]?.bid || [], commonTimestamps);

        const midlineA = askA.map((a, i) => a !== null && bidA[i] !== null ? (a + bidA[i]) / 2 : null);
        const midlineB = askB.map((a, i) => a !== null && bidB[i] !== null ? (a + bidB[i]) / 2 : null);




        const newChartData = {
          labels: commonTimestamps,
          datasets: view === 'ask_bid'
            ? [
                { label: `${brokerA} ${symbolA} Ask`, data: askA, borderColor: '#1f77b4', yAxisID: 'y1', spanGaps: true, pointRadius: 2 },
                { label: `${brokerA} ${symbolA} Bid`, data: bidA, borderColor: '#1f77b4', borderDash: [5, 5], yAxisID: 'y1', spanGaps: true, pointRadius: 2 },
                { label: `${brokerB} ${symbolB} Ask`, data: askB, borderColor: '#ff7f0e', yAxisID: 'y2', spanGaps: true, pointRadius: 2 },
                { label: `${brokerB} ${symbolB} Bid`, data: bidB, borderColor: '#ff7f0e', borderDash: [5, 5], yAxisID: 'y2', spanGaps: true, pointRadius: 2 },
              ]
            : [
                { label: `${brokerA} ${symbolA} Midline`, data: midlineA, borderColor: '#1f77b4', yAxisID: 'y1', spanGaps: true, pointRadius: 2 },
                { label: `${brokerB} ${symbolB} Midline`, data: midlineB, borderColor: '#ff7f0e', yAxisID: 'y2', spanGaps: true, pointRadius: 2 },
              ],
        };



        setChartData(newChartData);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData(); // Initial fetch
    const intervalId = setInterval(fetchData, 600000); // Poll every 10 minutes

    return () => {
      clearInterval(intervalId); // Cleanup interval
      
    };
  }, [brokerA, symbolA, brokerB, symbolB, timeRange, spreadPoints, view]);

  // Save zoom range
  const saveZoomRange = (chart) => {
    const xScale = chart.scales?.x;
    if (!xScale) return;
    const { min, max } = xScale;
    if (min == null || max == null) return;

    zoomRangeRef.current = { min, max };
    try {
      localStorage.setItem(zoomKey, JSON.stringify({ min, max }));
    } catch (e) {}
    console.log("Zoom range saved:", { min, max });
  };

  // Reset zoom
  const handleResetZoom = () => {
    const chart = chartRef.current;
    if (chart) {
      chart.resetZoom();
      zoomRangeRef.current = null;
      localStorage.removeItem(zoomKey);
      console.log("Zoom reset");
    }
  };

  // Restore zoom or default last 5 minutes
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    const savedZoom = localStorage.getItem(zoomKey);
    if (savedZoom) {
      const { min, max } = JSON.parse(savedZoom);
      zoomRangeRef.current = { min, max };
      chart.options.scales.x.min = min;
      chart.options.scales.x.max = max;
      chart.update();
      console.log("Zoom range restored:", { min, max });
      return;
    }

    const labels = chartData?.labels || [];
    if (labels.length) {
      const lastTime = Date.parse(labels[labels.length - 1]);
      const defaultWindowMs = 5 * 60 * 1000;
      const min = Math.max(Date.parse(labels[0]), lastTime - defaultWindowMs);
      chart.options.scales.x.min = min;
      chart.options.scales.x.max = lastTime;
      chart.update();
    }
  }, [chartData, zoomKey]); // ✅ zoomKey now stable, ESLint happy

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      tooltip: {
        callbacks: {
          label: (context) => `${context.dataset.label}: ${Number(context.parsed.y).toFixed(5)}`
        },
      },
      legend: { position: 'top' },
      title: { display: true, text: `${brokerA} ${symbolA} vs ${brokerB} ${symbolB}` },
      zoom: {
        pan: {
          enabled: true,
          mode: 'x',  // Enable horizontal panning (scrolling)
        },
        zoom: {
          wheel: {
            enabled: true,
          },
          pinch: {
            enabled: true,
          },
          mode: 'x',
          onZoomComplete: ({ chart }) => {
            saveZoomRange(chart);
          } // Enable horizontal zooming
        },
      },
    },
    scales: {
      y1: { type: 'linear', position: 'left', title: { display: true, text: `Price (${symbolA})` }, grid: { drawOnChartArea: false } },
      y2: { type: 'linear', position: 'right', title: { display: true, text: `Price (${symbolB})` }, grid: { drawOnChartArea: false } },
      x: { type: 'time', time: { unit: 'second' }, title: { display: true, text: 'Time' }, ticks: {
      maxTicksLimit: 5,
      autoSkip: true,
      maxRotation: 0,
      minRotation: 0,
      callback: (value) => {
        const date = new Date(value);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      }
      } },
    },
    height: 400, // Fixed height for better scrolling
  };

  return (
    <div style={{ position: 'relative', height: '400px', overflow: 'hidden' }}>
      <div>
        <label>Toggle View: </label>
        <select className="select-style"  value={view} onChange={(e) => setView(e.target.value)}>
          <option value="ask_bid">Show Ask/Bid Prices</option>
          <option value="midline">Show Midlines</option>
        </select>
      </div>
      {chartData && <Line ref={chartRef} data={chartData} options={options} />}
      <button onClick={handleResetZoom}>Reset Zoom</button>

    </div>
  );
};

export default ChartComponent;