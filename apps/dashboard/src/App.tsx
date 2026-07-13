import { Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { OverviewPage } from "./pages/OverviewPage";
import { EntityBrowserPage } from "./pages/EntityBrowserPage";
import { ProductsPage } from "./pages/ProductsPage";
import { ProductDetailPage } from "./pages/ProductDetailPage";
import { SearchPage } from "./pages/SearchPage";
import { ReviewsPage } from "./pages/ReviewsPage";
import { ReviewDetailPage } from "./pages/ReviewDetailPage";
import { RecentChangesPage } from "./pages/RecentChangesPage";
import { ContentAgentPage } from "./pages/ContentAgentPage";
import { GTMAgentPage } from "./pages/GTMAgentPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/entities" element={<EntityBrowserPage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/products/:slug" element={<ProductDetailPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/reviews" element={<ReviewsPage />} />
        <Route path="/reviews/:runId" element={<ReviewDetailPage />} />
        <Route path="/changes" element={<RecentChangesPage />} />
        <Route path="/agents/content" element={<ContentAgentPage />} />
        <Route path="/agents/gtm" element={<GTMAgentPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
