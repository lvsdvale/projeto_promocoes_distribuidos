import { useState } from 'react';
import api from '../api';

export default function Loja() {
  const [nome, setNome] = useState('');
  const [categoria, setCategoria] = useState('');

  const criarPromocao = async (e) => {
    e.preventDefault();
    const idGerado = crypto.randomUUID(); 
    const payload = {
      id: idGerado, 
      nome: nome, 
      categoria: categoria 
    };

    try {
      await api.post('/promotion/create', payload);
      alert('Promoção publicada com sucesso!');
      setNome('');
      setCategoria('');
    } catch (error) {
      alert('Erro ao publicar: ' + (error.response?.data?.message || error.message));
    }
  };
  return (
    <div className="card">
      <h2>Painel da Loja</h2>
      <form onSubmit={criarPromocao}>
        <div className="form-group">
          <label>Nome do Produto</label>
          <input placeholder="Ex: Notebook Gamer" value={nome} onChange={e => setNome(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Categoria</label>
          <input placeholder="Ex: informatica" value={categoria} onChange={e => setCategoria(e.target.value)} required />
        </div>
        <button type="submit" className="btn-primary">Publicar Promoção</button>
      </form>
    </div>
  );
}