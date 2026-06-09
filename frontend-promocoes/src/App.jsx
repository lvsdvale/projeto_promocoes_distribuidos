// src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Cadastro from './pages/Cadastro'; 
import Cliente from './pages/Cliente';
import Loja from './pages/Loja';
import './App.css'; // Importando nosso estilo bonitinho!

function App() {
  return (
    <BrowserRouter>

      <header className="header">
        <h1>Sistema de Promoções - Hot Deals</h1>
      </header>

      <main className="container">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/cadastro" element={<Cadastro />} />
          <Route path="/cliente" element={<Cliente />} />
          <Route path="/loja" element={<Loja />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;