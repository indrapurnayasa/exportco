// Vercel Frontend Integration with SSL
// Use this code in your Vercel frontend with Let's Encrypt SSL

// Configuration - Update with your domain
const API_BASE_URL = 'https://yourdomain.com'; // Replace with your actual domain

// 1. Fast Health Check (for connectivity testing)
async function checkAPIConnectivity() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
            // 3 second timeout for health check
            signal: AbortSignal.timeout(3000)
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ API Connectivity: OK', data);
            return true;
        } else {
            console.error('❌ API Connectivity: Failed', response.status);
            return false;
        }
    } catch (error) {
        console.error('❌ API Connectivity Error:', error);
        return false;
    }
}

// 2. Optimized Seasonal Trend API Call
async function getSeasonalTrend(endDate = null) {
    try {
        const url = new URL(`${API_BASE_URL}/api/v1/export/seasonal-trend`);
        if (endDate) {
            url.searchParams.append('endDate', endDate);
        }
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            // 8 second timeout (within Vercel free tier limit)
            signal: AbortSignal.timeout(8000)
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Seasonal Trend Data:', data);
            return data;
        } else {
            console.error('❌ Seasonal Trend Error:', response.status, response.statusText);
            throw new Error(`API Error: ${response.status}`);
        }
    } catch (error) {
        if (error.name === 'TimeoutError') {
            console.error('⏱️ Request timeout - API took too long to respond');
            throw new Error('Request timeout. Please try again.');
        }
        console.error('❌ Seasonal Trend Request Error:', error);
        throw error;
    }
}

// 3. Country Demand API Call
async function getCountryDemand(endDate = null) {
    try {
        const url = new URL(`${API_BASE_URL}/api/v1/export/country-demand`);
        if (endDate) {
            url.searchParams.append('endDate', endDate);
        }
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            // 8 second timeout
            signal: AbortSignal.timeout(8000)
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Country Demand Data:', data);
            return data;
        } else {
            console.error('❌ Country Demand Error:', response.status, response.statusText);
            throw new Error(`API Error: ${response.status}`);
        }
    } catch (error) {
        if (error.name === 'TimeoutError') {
            console.error('⏱️ Request timeout - API took too long to respond');
            throw new Error('Request timeout. Please try again.');
        }
        console.error('❌ Country Demand Request Error:', error);
        throw error;
    }
}

// 4. Top Commodity API Call
async function getTopCommodity(endDate = null, countryId = null) {
    try {
        const url = new URL(`${API_BASE_URL}/api/v1/export/top-commodity-by-country`);
        if (endDate) {
            url.searchParams.append('endDate', endDate);
        }
        if (countryId) {
            url.searchParams.append('countryId', countryId);
        }
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            // 8 second timeout
            signal: AbortSignal.timeout(8000)
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Top Commodity Data:', data);
            return data;
        } else {
            console.error('❌ Top Commodity Error:', response.status, response.statusText);
            throw new Error(`API Error: ${response.status}`);
        }
    } catch (error) {
        if (error.name === 'TimeoutError') {
            console.error('⏱️ Request timeout - API took too long to respond');
            throw new Error('Request timeout. Please try again.');
        }
        console.error('❌ Top Commodity Request Error:', error);
        throw error;
    }
}

// 5. React Hook Example
function useAPI() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [data, setData] = useState(null);
    
    const fetchData = async (apiFunction, ...args) => {
        setLoading(true);
        setError(null);
        
        try {
            // First check connectivity
            const isConnected = await checkAPIConnectivity();
            if (!isConnected) {
                throw new Error('Cannot connect to API server');
            }
            
            // Then fetch actual data
            const result = await apiFunction(...args);
            setData(result);
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    };
    
    return { loading, error, data, fetchData };
}

// 6. React Component Example
function SeasonalTrendComponent() {
    const { loading, error, data, fetchData } = useAPI();
    const [endDate, setEndDate] = useState('31-12-2024');

    const handleFetchData = async () => {
        try {
            await fetchData(getSeasonalTrend, endDate);
        } catch (err) {
            console.error('Failed to fetch data:', err);
        }
    };

    return (
        <div>
            <h2>Seasonal Trend Data</h2>
            <input
                type="text"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                placeholder="End Date (DD-MM-YYYY)"
            />
            <button onClick={handleFetchData} disabled={loading}>
                {loading ? 'Loading...' : 'Fetch Data'}
            </button>
            
            {error && <div style={{color: 'red'}}>Error: {error}</div>}
            
            {data && (
                <div>
                    <h3>Results:</h3>
                    <pre>{JSON.stringify(data, null, 2)}</pre>
                </div>
            )}
        </div>
    );
}

// 7. Usage Examples
async function exampleUsage() {
    try {
        // Check connectivity first
        const isConnected = await checkAPIConnectivity();
        if (!isConnected) {
            console.error('❌ Cannot connect to API');
            return;
        }
        
        // Fetch seasonal trend data
        const seasonalData = await getSeasonalTrend('31-12-2024');
        console.log('Seasonal Trend:', seasonalData);
        
        // Fetch country demand data
        const countryData = await getCountryDemand('31-12-2024');
        console.log('Country Demand:', countryData);
        
        // Fetch top commodity data
        const commodityData = await getTopCommodity('31-12-2024', 'ID');
        console.log('Top Commodity:', commodityData);
        
    } catch (error) {
        console.error('❌ API Error:', error.message);
    }
}

// 8. Vercel Environment Variables (add to your Vercel project)
/*
API_BASE_URL=https://yourdomain.com
API_TIMEOUT=8000
NODE_TLS_REJECT_UNAUTHORIZED=0
*/

// 9. Next.js API Route Example (for server-side calls)
// pages/api/seasonal-trend.js
export default async function handler(req, res) {
    try {
        const { endDate } = req.query;
        
        const response = await fetch(`${API_BASE_URL}/api/v1/export/seasonal-trend?endDate=${endDate}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
            signal: AbortSignal.timeout(8000)
        });
        
        if (response.ok) {
            const data = await response.json();
            res.status(200).json(data);
        } else {
            res.status(response.status).json({ error: 'API request failed' });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
}

// Export functions for use in your frontend
export {
    checkAPIConnectivity,
    getSeasonalTrend,
    getCountryDemand,
    getTopCommodity,
    useAPI,
    SeasonalTrendComponent,
    exampleUsage
};