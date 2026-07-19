import { Routes, Route, Navigate } from "react-router-dom";
import InboxPage from "./pages/InboxPage";
import FounderDetailPage from "./pages/FounderDetailPage";
import ThesisPage from "./pages/ThesisPage";
import OutboundPage from "./pages/OutboundPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<InboxPage />} />
      <Route path="/founders/:founderId" element={<FounderDetailPage />} />
      <Route path="/thesis" element={<ThesisPage />} />
      <Route path="/outbound" element={<OutboundPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
