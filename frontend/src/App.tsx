import React, { useState, useRef } from 'react';
import { Container, Typography, Box, TextField, Button, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, LinearProgress, IconButton, InputAdornment } from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import DownloadIcon from '@mui/icons-material/Download';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import * as XLSX from 'xlsx';
import axios from 'axios';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Collapse from '@mui/material/Collapse';
import CloseIcon from '@mui/icons-material/Close';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

function parseUrls(text: string): string[] {
  return text
    .split(/[\n,]+/)
    .map(url => url.trim())
    .filter(url => url.length > 0);
}

const App: React.FC = () => {
  const [categoryInput, setCategoryInput] = useState('');
  const [categoryFileName, setCategoryFileName] = useState('');
  const [categoryUrls, setCategoryUrls] = useState<string[]>([]);
  const [limit, setLimit] = useState<number | ''>('');
  const [scraping, setScraping] = useState(false);
  const [progress, setProgress] = useState<number>(0);
  const [productUrls, setProductUrls] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Product details state
  const [detailsScraping, setDetailsScraping] = useState(false);
  const [detailsProgress, setDetailsProgress] = useState<number>(0);
  const [productDetails, setProductDetails] = useState<any[]>([]);
  const [detailsError, setDetailsError] = useState<string | null>(null);

  // Log console state
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  // Simulate log appending (replace with SSE/polling for real backend logs)
  const appendLog = (msg: string) => setLogs(logs => [...logs, msg]);

  // Example: append logs on scraping start/finish (extend to backend events as needed)
  // Abort controllers for cancellation
  const productUrlsAbortRef = useRef<AbortController | null>(null);
  const productDetailsAbortRef = useRef<AbortController | null>(null);

  // Cancel scraping handlers
  const handleCancelProductUrls = () => {
    if (productUrlsAbortRef.current) {
      productUrlsAbortRef.current.abort();
      appendLog('Product URLs scraping cancelled by user.');
      setScraping(false);
    }
    // Placeholder: call backend cancel endpoint if needed
    // axios.post(`${BACKEND_URL}/cancel-scrape`, { jobId: ... })
  };
  const handleCancelProductDetails = () => {
    if (productDetailsAbortRef.current) {
      productDetailsAbortRef.current.abort();
      appendLog('Product details scraping cancelled by user.');
      setDetailsScraping(false);
    }
    // Placeholder: call backend cancel endpoint if needed
    // axios.post(`${BACKEND_URL}/cancel-scrape`, { jobId: ... })
  };

  // Update scraping handlers to use AbortController
  const handleScrapeProductUrls = async () => {
    setScraping(true);
    setError(null);
    setProgress(0);
    setProductUrls([]);
    appendLog('Started scraping product URLs...');
    const abortController = new AbortController();
    productUrlsAbortRef.current = abortController;
    try {
      const response = await axios.post(`${BACKEND_URL}/scrape-product-urls`, {
        categoryUrls,
        limit: limit === '' ? undefined : limit,
      }, {
        onDownloadProgress: (progressEvent) => {
          if (progressEvent.total) {
            setProgress(Math.round((progressEvent.loaded / progressEvent.total) * 100));
          }
        },
        signal: abortController.signal,
      });
      setProductUrls(response.data.productUrls || response.data);
      appendLog(`Scraped ${response.data.productUrls?.length || response.data.length} product URLs.`);
    } catch (err: any) {
      if (axios.isCancel(err) || err.code === 'ERR_CANCELED') {
        setError('Scraping cancelled.');
        appendLog('Scraping product URLs cancelled.');
      } else {
        setError(err.response?.data?.message || err.message || 'Failed to scrape product URLs.');
        appendLog('Error scraping product URLs.');
      }
    } finally {
      setScraping(false);
      setProgress(100);
      appendLog('Finished scraping product URLs.');
      productUrlsAbortRef.current = null;
    }
  };

  // Download product URLs as Excel
  const handleDownloadExcel = () => {
    const ws = XLSX.utils.aoa_to_sheet([
      ['Product URL'],
      ...productUrls.map(url => [url]),
    ]);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Product URLs');
    XLSX.writeFile(wb, 'product_urls.xlsx');
  };

  // Reset inputs/outputs
  const handleReset = () => {
    setCategoryInput('');
    setCategoryFileName('');
    setCategoryUrls([]);
    setLimit('');
    setProductUrls([]);
    setError(null);
    setProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Handle file upload (CSV/XLSX)
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCategoryFileName(file.name);
    const reader = new FileReader();
    reader.onload = (evt) => {
      const data = evt.target?.result;
      if (!data) return;
      let urls: string[] = [];
      if (file.name.endsWith('.csv')) {
        const text = data as string;
        urls = parseUrls(text);
      } else if (file.name.endsWith('.xlsx')) {
        const workbook = XLSX.read(data, { type: 'binary' });
        const sheet = workbook.Sheets[workbook.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json<any[]>(sheet, { header: 1 });
        urls = rows
          .flatMap((row: any) => Array.isArray(row) ? row : [row])
          .map((cell: any) => (typeof cell === 'string' ? cell : String(cell)))
          .map(url => url.trim())
          .filter(url => url.length > 0 && url.startsWith('http'));
      }
      setCategoryUrls(urls);
      setCategoryInput(urls.join('\n'));
    };
    if (file.name.endsWith('.csv')) {
      reader.readAsText(file);
    } else if (file.name.endsWith('.xlsx')) {
      reader.readAsBinaryString(file);
    }
  };

  // Handle manual input
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCategoryInput(e.target.value);
    setCategoryUrls(parseUrls(e.target.value));
  };

  // Handle limit input
  const handleLimitChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setLimit(val === '' ? '' : Math.max(1, parseInt(val)));
  };

  // Scrape product details
  const handleScrapeProductDetails = async () => {
    setDetailsScraping(true);
    setDetailsError(null);
    setDetailsProgress(0);
    setProductDetails([]);
    appendLog('Started scraping product details...');
    const abortController = new AbortController();
    productDetailsAbortRef.current = abortController;
    try {
      const response = await axios.post(`${BACKEND_URL}/scrape-product-details`, {
        productUrls,
      }, {
        onDownloadProgress: (progressEvent) => {
          if (progressEvent.total) {
            setDetailsProgress(Math.round((progressEvent.loaded / progressEvent.total) * 100));
          }
        },
        signal: abortController.signal,
      });
      setProductDetails(response.data.productDetails || response.data);
      appendLog(`Scraped details for ${response.data.productDetails?.length || response.data.length} products.`);
    } catch (err: any) {
      if (axios.isCancel(err) || err.code === 'ERR_CANCELED') {
        setDetailsError('Scraping cancelled.');
        appendLog('Scraping product details cancelled.');
      } else {
        setDetailsError(err.response?.data?.message || err.message || 'Failed to scrape product details.');
        appendLog('Error scraping product details.');
      }
    } finally {
      setDetailsScraping(false);
      setDetailsProgress(100);
      appendLog('Finished scraping product details.');
      productDetailsAbortRef.current = null;
    }
  };

  // Download product details as Excel
  const handleDownloadDetailsExcel = () => {
    const ws = XLSX.utils.aoa_to_sheet([
      ['URL', 'Product Name', 'Price', 'Currency'],
      ...productDetails.map(d => [d.url, d.product_name || d.productName, d.price, d.currency]),
    ]);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Product Details');
    XLSX.writeFile(wb, 'product_details.xlsx');
  };

  // Reset product details output
  const handleResetDetails = () => {
    setProductDetails([]);
    setDetailsError(null);
    setDetailsProgress(0);
  };

  // Add a ref for the log box
  const logBoxRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest log
  React.useEffect(() => {
    if (logBoxRef.current) {
      logBoxRef.current.scrollTop = logBoxRef.current.scrollHeight;
    }
  }, [logs, showLogs]);

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom align="center">
        Amazon Scraper UI
      </Typography>
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          1. Enter Amazon Category URLs
        </Typography>
        <TextField
          label="Category URLs (comma or newline separated)"
          multiline
          minRows={3}
          fullWidth
          value={categoryInput}
          onChange={handleInputChange}
          disabled={scraping}
          margin="normal"
        />
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Button
            variant="outlined"
            component="label"
            startIcon={<UploadFileIcon />}
            disabled={scraping}
          >
            Upload CSV/XLSX
            <input
              type="file"
              accept=".csv,.xlsx"
              hidden
              ref={fileInputRef}
              onChange={handleFileUpload}
            />
          </Button>
          <Typography variant="body2" color="text.secondary">
            {categoryFileName}
          </Typography>
          <TextField
            label="Limit (optional)"
            type="number"
            value={limit}
            onChange={handleLimitChange}
            disabled={scraping}
            InputProps={{ inputProps: { min: 1 } }}
            sx={{ width: 150 }}
          />
          <Button
            variant="contained"
            onClick={handleScrapeProductUrls}
            disabled={scraping || categoryUrls.length === 0}
          >
            Start Scraping Product URLs
          </Button>
          {scraping && (
            <IconButton onClick={handleCancelProductUrls} color="error" sx={{ ml: 1 }}>
              <CloseIcon />
            </IconButton>
          )}
          <IconButton onClick={handleReset} disabled={scraping} color="secondary">
            <RestartAltIcon />
          </IconButton>
        </Box>
        {scraping && <LinearProgress sx={{ mb: 2 }} />}
        {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}
        {productUrls.length > 0 && (
          <Box>
            <Typography variant="subtitle1" sx={{ mt: 2 }}>
              Extracted Product URLs ({productUrls.length})
            </Typography>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadExcel}
              sx={{ mb: 1 }}
            >
              Download as Excel
            </Button>
            <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Product URL</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {productUrls.map((url, idx) => (
                    <TableRow key={idx}>
                      <TableCell sx={{ wordBreak: 'break-all' }}>{url}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </Paper>
      {/* Product Details Extraction Flow Placeholder */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          2. Product Details Extraction
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Button
            variant="contained"
            onClick={handleScrapeProductDetails}
            disabled={detailsScraping || productUrls.length === 0}
          >
            Start Scraping Product Details
          </Button>
          {detailsScraping && (
            <IconButton onClick={handleCancelProductDetails} color="error" sx={{ ml: 1 }}>
              <CloseIcon />
            </IconButton>
          )}
          <IconButton onClick={handleResetDetails} disabled={detailsScraping} color="secondary">
            <RestartAltIcon />
          </IconButton>
        </Box>
        {detailsScraping && <LinearProgress sx={{ mb: 2 }} />}
        {detailsError && <Typography color="error" sx={{ mb: 2 }}>{detailsError}</Typography>}
        {productDetails.length > 0 && (
          <Box>
            <Typography variant="subtitle1" sx={{ mt: 2 }}>
              Scraped Product Details ({productDetails.length})
            </Typography>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadDetailsExcel}
              sx={{ mb: 1 }}
            >
              Download as Excel
            </Button>
            <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>URL</TableCell>
                    <TableCell>Product Name</TableCell>
                    <TableCell>Price</TableCell>
                    <TableCell>Currency</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {productDetails.map((d, idx) => (
                    <TableRow key={idx}>
                      <TableCell sx={{ wordBreak: 'break-all' }}>{d.url}</TableCell>
                      <TableCell>{d.product_name || d.productName}</TableCell>
                      <TableCell>{d.price}</TableCell>
                      <TableCell>{d.currency}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </Paper>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={() => setShowLogs(l => !l)}>
          <ExpandMoreIcon sx={{ transform: showLogs ? 'rotate(180deg)' : 'rotate(0deg)', transition: '0.2s' }} />
          <Typography variant="subtitle1" sx={{ ml: 1 }}>
            {showLogs ? 'Hide' : 'Show'} Logs / Console
          </Typography>
        </Box>
        <Collapse in={showLogs}>
          <Box sx={{ mt: 2, maxHeight: 200, overflow: 'auto', bgcolor: '#111', color: '#0f0', fontFamily: 'monospace', fontSize: 14, p: 2, borderRadius: 1 }}>
            {logs.length === 0 ? <span>No logs yet.</span> : logs.map((log, idx) => <div key={idx}>{log}</div>)}
          </Box>
        </Collapse>
      </Paper>
    </Container>
  );
};

export default App;
