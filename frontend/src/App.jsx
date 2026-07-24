import { useState, useEffect } from 'react'
import ProductInventory from './VistaInventario'

function App() {
  // 1. Creamos un espacio en la memoria (estado) para guardar los productos
  const [productosReales, setProductosReales] = useState([])

  // 2. Esta función se ejecuta una sola vez cuando la página carga
  useEffect(() => {
    // 3. Vamos a la "Cocina" (puerto 8000) a pedir los ingredientes
    fetch("http://127.0.0.1:8000/api/productos")
      .then(respuesta => respuesta.json()) // 4. Transformamos la respuesta
      .then(datos => setProductosReales(datos)) // 5. Los guardamos en la memoria
  }, [])

  return (
    <div className="bg-gray-100 min-h-screen p-8">
      {/* 6. Le pasamos los productos reales a la tabla bonita de Claude */}
      <ProductInventory products={productosReales} />
    </div>
  )
}

export default App