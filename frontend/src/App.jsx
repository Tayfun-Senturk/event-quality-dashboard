import { useMemo, useState } from 'react';

import Layout from './components/Layout.jsx';
import Alerts from './pages/Alerts.jsx';
import Evaluation from './pages/Evaluation.jsx';
import MetricDetail from './pages/MetricDetail.jsx';
import Overview from './pages/Overview.jsx';

const pages = {
  overview: Overview,
  metricDetail: MetricDetail,
  alerts: Alerts,
  evaluation: Evaluation,
};

function App() {
  const [activePage, setActivePage] = useState('overview');
  const ActivePage = useMemo(() => pages[activePage] ?? Overview, [activePage]);

  return (
    <Layout activePage={activePage} onNavigate={setActivePage}>
      <ActivePage />
    </Layout>
  );
}

export default App;

