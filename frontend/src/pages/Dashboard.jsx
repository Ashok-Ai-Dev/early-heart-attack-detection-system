import React, { useState, useEffect, useRef } from 'react';
import { predictRisk, getHistory } from '../services/api';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import html2pdf from 'html2pdf.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const Dashboard = ({ setAuth }) => {
  const [formData, setFormData] = useState({
    age: '', gender: 1, cp: 0, trestbps: '', chol: '',
    fbs: 0, bmi: '', exercise_level: 0, smoking: 'no', alcohol: 'no'
  });
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [historyItems, setHistoryItems] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  
  const printRef = useRef();

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const { history } = await getHistory();
      setHistoryItems(history || []);
    } catch (e) {
      console.warn("Could not load history");
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const logout = () => {
    localStorage.removeItem('token');
    setAuth(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const formattedData = {
        age: Number(formData.age),
        gender: Number(formData.gender),
        cp: Number(formData.cp),
        trestbps: Number(formData.trestbps),
        chol: Number(formData.chol),
        fbs: Number(formData.fbs),
        bmi: Number(formData.bmi),
        exercise_level: Number(formData.exercise_level),
        smoking: formData.smoking,
        alcohol: formData.alcohol
      };
      const res = await predictRisk(formattedData);
      setResult(res);
      fetchHistory(); // refresh history
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred during prediction.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = () => {
    const element = printRef.current;
    if (!element) return;
    const opt = {
      margin:       1,
      filename:     'CardioCare-Report.pdf',
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2 },
      jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(element).save();
  };

  const chartData = result ? {
    labels: ['Risk Probability Data', 'Safe'],
    datasets: [{
      data: [result.probability, 100 - result.probability],
      backgroundColor: [
        result.probability > 66 ? '#ef4444' : result.probability > 33 ? '#eab308' : '#22c55e',
        '#374151'
      ],
      borderWidth: 0,
      cutout: '80%'
    }]
  } : null;

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-6xl mx-auto flex justify-between items-center mb-8">
        <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
          CardioCare AI
        </h1>
        <div className="space-x-4">
          <button onClick={() => setShowHistory(!showHistory)} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded text-sm font-semibold transition-colors">
            {showHistory ? 'Hide History' : 'View History'}
          </button>
          <button onClick={logout} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm font-semibold transition-colors">
            Logout
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Form Section */}
        <div className="bg-gray-800 p-8 rounded-2xl shadow-xl border border-gray-700">
          <h2 className="text-xl font-bold mb-6 text-gray-200 border-b border-gray-700 pb-2">Health Metrics</h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Age</label>
              <input type="number" name="age" required value={formData.age} onChange={handleChange} className="w-full p-2.5 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-white" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Gender</label>
              <select name="gender" value={formData.gender} onChange={handleChange} className="w-full p-2.5 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-white">
                <option value={1}>Male</option>
                <option value={0}>Female</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Chest Pain Type</label>
              <select name="cp" value={formData.cp} onChange={handleChange} className="w-full p-2.5 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-white">
                <option value={0}>Typical Angina</option>
                <option value={1}>Atypical Angina</option>
                <option value={2}>Non-anginal Pain</option>
                <option value={3}>Asymptomatic</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Resting Blood Pressure</label>
              <input type="number" name="trestbps" required value={formData.trestbps} onChange={handleChange} className="w-full p-2.5 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-white" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Cholesterol</label>
              <input type="number" name="chol" required value={formData.chol} onChange={handleChange} className="w-full p-2.5 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-white" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Fasting Blood Sugar {'>'} 120 mg/dl</label>
              <select name="fbs" value={formData.fbs} onChange={handleChange} className="w-full p-2.5 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-white">
                <option value={0}>False</option>
                <option value={1}>True</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">BMI</label>
              <input type="number" step="0.1" name="bmi" required value={formData.bmi} onChange={handleChange} className="w-full p-2.5 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-white" />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Exercise Induced Angina</label>
              <select name="exercise_level" value={formData.exercise_level} onChange={handleChange} className="w-full p-2.5 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-white">
                <option value={0}>No</option>
                <option value={1}>Yes</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Smoking</label>
              <select name="smoking" value={formData.smoking} onChange={handleChange} className="w-full p-2.5 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-white">
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Alcohol</label>
              <select name="alcohol" value={formData.alcohol} onChange={handleChange} className="w-full p-2.5 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 text-white">
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </div>
            
            <div className="md:col-span-2 pt-4">
              <button disabled={loading} type="submit" className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3 rounded-lg shadow-lg transform transition hover:-translate-y-0.5">
                {loading ? 'Analyzing...' : 'Predict Risk'}
              </button>
            </div>
          </form>
        </div>

        {/* Dynamic Section (Results or History) */}
        {showHistory ? (
           <div className="bg-gray-800 p-8 rounded-2xl shadow-xl border border-gray-700 overflow-y-auto max-h-[700px]">
             <h2 className="text-2xl font-bold mb-6 text-indigo-400">Your Prediction History</h2>
             {historyItems.length === 0 ? (
               <p className="text-gray-500">No predictions made yet.</p>
             ) : (
               <div className="space-y-4">
                 {historyItems.map((item, idx) => (
                   <div key={idx} className="bg-gray-700/50 p-4 rounded-xl border border-gray-600">
                     <p className="text-lg font-bold">
                        Risk: <span className={item.risk === 'High' ? 'text-red-500' : item.risk === 'Medium' ? 'text-yellow-500' : 'text-green-500'}>{item.risk} ({item.probability}%)</span>
                     </p>
                     <p className="text-sm text-gray-400 mb-2">Date: {new Date(item.timestamp).toLocaleString()}</p>
                     <p className="text-sm text-gray-300"><b>Tip:</b> {item.suggestion.split('|')[0]}</p>
                   </div>
                 ))}
               </div>
             )}
           </div>
        ) : (
        <div className="bg-gray-800 p-8 rounded-2xl shadow-xl border border-gray-700 flex flex-col items-center justify-center relative overflow-hidden">
          {error && <div className="text-red-400 mb-4 bg-red-900/30 p-4 rounded-lg w-full text-center border border-red-800">{error}</div>}
          
          {!result && !error && (
            <div className="text-center text-gray-500 flex flex-col items-center">
              <svg className="w-24 h-24 mb-6 text-gray-700/50" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path></svg>
              <p className="text-lg">Submit your details to see your heart risk analysis</p>
            </div>
          )}

          {result && (
            <div className="w-full animate-fade-in-up">
              <div ref={printRef} className="bg-gray-800 p-4">
                <h2 className="text-3xl font-bold text-center mb-8 tracking-tight">Analysis Result</h2>
                
                <div className="flex flex-col items-center justify-center mb-8 relative">
                  <div className="w-48 h-48">
                    <Doughnut data={chartData} options={{ maintainAspectRatio: true }} />
                  </div>
                  <div className="absolute flex flex-col items-center justify-center inset-0">
                    <span className="text-4xl font-extrabold">{result.probability}%</span>
                    <span className={`text-sm font-bold tracking-wider uppercase mt-1 ${result.risk === 'High' ? 'text-red-500' : result.risk === 'Medium' ? 'text-yellow-500' : 'text-green-500'}`}>
                      {result.risk} Risk
                    </span>
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="bg-gray-700/50 p-6 rounded-xl border border-gray-600">
                    <h3 className="text-emerald-400 font-bold mb-2 flex items-center">
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                      Health Suggestions
                    </h3>
                    <p className="text-gray-300 leading-relaxed text-sm">
                      {result.suggestion.split('|').map((s, idx) => <span key={idx} className="block mt-1">• {s.trim()}</span>)}
                    </p>
                  </div>

                  <div className="bg-gray-700/50 p-6 rounded-xl border border-gray-600">
                    <h3 className="text-blue-400 font-bold mb-2 flex items-center">
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
                      Diet Recommendation
                    </h3>
                    <p className="text-gray-300 leading-relaxed text-sm">{result.diet}</p>
                  </div>
                </div>
              </div>
              <button onClick={handleDownloadPDF} className="mt-6 w-full py-3 bg-red-600 hover:bg-red-500 text-white font-bold rounded-lg shadow transition">
                Download Report as PDF
              </button>
            </div>
          )}
        </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;

