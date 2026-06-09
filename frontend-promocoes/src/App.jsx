import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Cadastro from './pages/Cadastro'; 
import Cliente from './pages/Cliente';
import Loja from './pages/Loja';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/cadastro" element={<Cadastro />} />
        <Route path="/cliente" element={<Cliente />} />
        <Route path="/loja" element={<Loja />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;