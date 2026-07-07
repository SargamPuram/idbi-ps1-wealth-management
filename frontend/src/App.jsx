import { BrowserRouter, Routes, Route } from "react-router-dom";
import { CustomerProvider } from "./context/CustomerContext";
import BottomNav from "./components/BottomNav";
import AvatarChat from "./pages/AvatarChat";
import Portfolio from "./pages/Portfolio";
import Goals from "./pages/Goals";
import Market from "./pages/Market";
import Products from "./pages/Products";

function PageWrap({ children }) {
  return <div className="page-content">{children}</div>;
}

export default function App() {
  return (
    <CustomerProvider>
      <BrowserRouter basename='/ps1'>
        <div className="app-shell">
          <Routes>
            <Route path="/" element={<AvatarChat />} />
            <Route
              path="/portfolio"
              element={
                <PageWrap>
                  <Portfolio />
                </PageWrap>
              }
            />
            <Route
              path="/goals"
              element={
                <PageWrap>
                  <Goals />
                </PageWrap>
              }
            />
            <Route
              path="/market"
              element={
                <PageWrap>
                  <Market />
                </PageWrap>
              }
            />
            <Route
              path="/products"
              element={
                <PageWrap>
                  <Products />
                </PageWrap>
              }
            />
          </Routes>
          <BottomNav />
        </div>
      </BrowserRouter>
    </CustomerProvider>
  );
}

