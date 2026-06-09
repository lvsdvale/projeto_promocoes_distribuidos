import { useState } from 'react';
import api from '../api';

export default function Loja() {
  const [nome, setNome] = useState('');
  const [categoria, setCategoria] = useState('');
  const [id, setId] = useState('');

  const criarPromocao = async (e) => {
    e.preventDefault();
    
    const dadosPromocao = { id, nome, categoria };
    
    // NOTA: Para o trabalho, você precisa gerar a 'Signature' aqui via RSA (usando a private key da loja)
    // ou modificar o gateway para aceitar sem assinatura temporariamente enquanto desenvolve o front.
    const payload = {
      dados: dadosPromocao,
      Signature: "ASSINATURA_BASE64_GERADA_AQUI" 
    };

    try {
      await api.post('/promotion/create', payload);
      alert('Promoção enviada!');
    } catch (error) {
      alert('Erro: ' + error.response?.data?.message);
    }
  };

  return (
    <form onSubmit={criarPromocao}>
      <h1>Painel da Loja</h1>
      <input placeholder="ID da Promoção" onChange={e => setId(e.target.value)} required />
      <input placeholder="Nome do Produto" onChange={e => setNome(e.target.value)} required />
      <input placeholder="Categoria (ex: smartphone)" onChange={e => setCategoria(e.target.value)} required />
      <button type="submit">Publicar Promoção</button>
    </form>
  );
}