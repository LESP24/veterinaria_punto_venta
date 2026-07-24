import { useState, useMemo, useEffect, useRef } from "react";

/* ─────────────────────────── Sample data ─────────────────────────── */
const SAMPLE_DATA = [
  { codigo: "J2E14295", nombre: "4 Plex Recovery Complemento Vitaminico 30gr", categoria: "General",      laboratorio: "- Sin Departamento -", costo_referencia: 300.0,  precio_publico: 450.0, precio_mayoreo: 345.0, stock_minimo: 1 },
  { codigo: "BAN-4",    nombre: "BANDANA NUMERO 4",                             categoria: "General",      laboratorio: "accesorios",          costo_referencia: 50.0,   precio_publico: 120.0, precio_mayoreo: 0.0,   stock_minimo: 1 },
  { codigo: "38100138", nombre: "CANINE/EN/2.72kg",                             categoria: "General",      laboratorio: "CATSAVET",            costo_referencia: 526.64, precio_publico: 750.0, precio_mayoreo: 620.0, stock_minimo: 1 },
  { codigo: "VIT-C200", nombre: "Vitamina C 200mg Masticable Animales",         categoria: "Vitaminas",    laboratorio: "NutriVet",            costo_referencia: 85.0,   precio_publico: 160.0, precio_mayoreo: 130.0, stock_minimo: 5 },
  { codigo: "ANT-001",  nombre: "Antibiótico Amoxicilina 500mg Canino",         categoria: "Medicamentos", laboratorio: "VetPharma",           costo_referencia: 220.0,  precio_publico: 380.0, precio_mayoreo: 310.0, stock_minimo: 3 },
  { codigo: "SHA-PERR", nombre: "Shampoo Medicado Antipulgas 500ml",            categoria: "Higiene",      laboratorio: "PetClean",            costo_referencia: 95.0,   precio_publico: 185.0, precio_mayoreo: 150.0, stock_minimo: 2 },
  { codigo: "COL-M5",   nombre: "Collar Antiparasitario Mediano 5 meses",       categoria: "Accesorios",   laboratorio: "Seresto",             costo_referencia: 310.0,  precio_publico: 520.0, precio_mayoreo: 440.0, stock_minimo: 4 },
];

const EMPTY_FORM = { codigo: "", nombre: "", categoria: "", laboratorio: "", costo_referencia: "", precio_publico: "", precio_mayoreo: "", stock_minimo: "" };

/* ─────────────────────────── Helpers ─────────────────────────── */
const fmt = (val) =>
  new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" }).format(val);

/* ─────────────────────────── Sub-components ─────────────────────────── */
const CategoryBadge = ({ categoria }) => {
  const colors = { General: "bg-slate-100 text-slate-600", Vitaminas: "bg-emerald-50 text-emerald-700", Medicamentos: "bg-blue-50 text-blue-700", Higiene: "bg-cyan-50 text-cyan-700", Accesorios: "bg-teal-50 text-teal-700" };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide ${colors[categoria] || "bg-gray-100 text-gray-600"}`}>
      {categoria}
    </span>
  );
};

const MarginBadge = ({ costo, precio }) => {
  if (!costo || !precio) return <span className="text-slate-300 text-xs">—</span>;
  const m = ((precio - costo) / precio) * 100;
  return <span className={`text-xs font-bold tabular-nums ${m >= 40 ? "text-emerald-600" : m >= 20 ? "text-amber-500" : "text-red-500"}`}>{m.toFixed(0)}%</span>;
};

const SortIcon = ({ direction }) => (
  <svg className="w-3 h-3 inline ml-1 opacity-60" viewBox="0 0 12 12" fill="currentColor">
    {direction === "asc" ? <path d="M6 2l4 7H2l4-7z"/> : direction === "desc" ? <path d="M6 10L2 3h8l-4 7z"/> : <><path d="M6 1l3 4H3l3-4z" opacity="0.4"/><path d="M6 11L3 7h6l-3 4z" opacity="0.4"/></>}
  </svg>
);

/* ─────────────────────────── Field config ─────────────────────────── */
const FORM_FIELDS = [
  { key: "codigo",           label: "Código",           type: "text",   placeholder: "Ej. ANT-001",  half: true,  required: true  },
  { key: "nombre",           label: "Nombre del producto", type: "text", placeholder: "Nombre completo", half: false, required: true  },
  { key: "categoria",        label: "Categoría",        type: "text",   placeholder: "Ej. Medicamentos", half: true, required: false },
  { key: "laboratorio",      label: "Laboratorio",      type: "text",   placeholder: "Ej. VetPharma",   half: true,  required: false },
  { key: "costo_referencia", label: "Costo de Referencia", type: "number", placeholder: "0.00", half: true,  required: false },
  { key: "precio_publico",   label: "Precio Público",   type: "number", placeholder: "0.00", half: true,  required: true  },
  { key: "precio_mayoreo",   label: "Precio Mayoreo",   type: "number", placeholder: "0.00", half: true,  required: false },
  { key: "stock_minimo",     label: "Stock Mínimo",     type: "number", placeholder: "1",    half: true,  required: false },
];

const COLUMNS = [
  { key: "codigo",           label: "Código",      sortable: true  },
  { key: "nombre",           label: "Producto",    sortable: true  },
  { key: "categoria",        label: "Categoría",   sortable: true  },
  { key: "laboratorio",      label: "Laboratorio", sortable: true  },
  { key: "costo_referencia", label: "Costo Ref.",  sortable: true  },
  { key: "precio_publico",   label: "P. Público",  sortable: true  },
  { key: "precio_mayoreo",   label: "P. Mayoreo",  sortable: true  },
  { key: "margen",           label: "Margen",      sortable: false },
];

/* ═══════════════════════════════════════════════════════════════
   MODAL: Agregar / Editar Producto
═══════════════════════════════════════════════════════════════ */
function ProductoModal({ isOpen, mode, initialData, onClose, onSave }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const firstInputRef = useRef(null);

  /* Populate form when modal opens */
  useEffect(() => {
    if (!isOpen) return;
    setErrors({});
    if (mode === "edit" && initialData) {
      setForm({
        codigo:           initialData.codigo           ?? "",
        nombre:           initialData.nombre           ?? "",
        categoria:        initialData.categoria        ?? "",
        laboratorio:      initialData.laboratorio      ?? "",
        costo_referencia: initialData.costo_referencia ?? "",
        precio_publico:   initialData.precio_publico   ?? "",
        precio_mayoreo:   initialData.precio_mayoreo   ?? "",
        stock_minimo:     initialData.stock_minimo     ?? "",
      });
    } else {
      setForm(EMPTY_FORM);
    }
    /* Auto-focus first input after open animation */
    setTimeout(() => firstInputRef.current?.focus(), 80);
  }, [isOpen, mode, initialData]);

  /* Close on Escape */
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  const handleChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: false }));
  };

  const validate = () => {
    const newErrors = {};
    FORM_FIELDS.forEach(({ key, required }) => {
      if (required && !String(form[key]).trim()) newErrors[key] = true;
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validate()) return;
    const parsed = {
      ...form,
      costo_referencia: parseFloat(form.costo_referencia) || 0,
      precio_publico:   parseFloat(form.precio_publico)   || 0,
      precio_mayoreo:   parseFloat(form.precio_mayoreo)   || 0,
      stock_minimo:     parseInt(form.stock_minimo)        || 1,
    };
    onSave(parsed, mode);
  };

  if (!isOpen) return null;

  const isEdit = mode === "edit";

  return (
    /* ── Backdrop ── */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(15, 30, 60, 0.45)", backdropFilter: "blur(4px)" }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      {/* ── Panel ── */}
      <div
        className="bg-white w-full max-w-xl rounded-2xl shadow-2xl flex flex-col overflow-hidden"
        style={{ maxHeight: "92vh", animation: "modalIn 0.18s cubic-bezier(0.34,1.56,0.64,1) both" }}
      >
        {/* Header */}
        <div className={`px-6 py-4 flex items-center justify-between border-b border-blue-100 ${isEdit ? "bg-gradient-to-r from-blue-50 to-teal-50" : "bg-gradient-to-r from-emerald-50 to-blue-50"}`}>
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center shadow-sm ${isEdit ? "bg-gradient-to-br from-blue-500 to-teal-400" : "bg-gradient-to-br from-emerald-500 to-teal-400"}`}>
              {isEdit ? (
                <svg className="w-4.5 h-4.5 text-white w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                </svg>
              ) : (
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4"/>
                </svg>
              )}
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-800 leading-none">
                {isEdit ? "Editar Producto" : "Nuevo Producto"}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {isEdit ? `Editando: ${initialData?.codigo}` : "Complete los campos del formulario"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg p-1.5 transition-all"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {/* Body / Form */}
        <div className="overflow-y-auto px-6 py-5 flex-1">
          <div className="grid grid-cols-2 gap-x-4 gap-y-4">
            {FORM_FIELDS.map((field, i) => (
              <div key={field.key} className={field.half ? "col-span-1" : "col-span-2"}>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5 tracking-wide uppercase">
                  {field.label}
                  {field.required && <span className="text-red-400 ml-0.5">*</span>}
                </label>
                <div className="relative">
                  {field.type === "number" && (
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm font-medium pointer-events-none">$</span>
                  )}
                  <input
                    ref={i === 0 ? firstInputRef : null}
                    type={field.type}
                    step={field.type === "number" ? "0.01" : undefined}
                    min={field.type === "number" ? "0" : undefined}
                    value={form[field.key]}
                    onChange={(e) => handleChange(field.key, e.target.value)}
                    placeholder={field.placeholder}
                    disabled={isEdit && field.key === "codigo"}
                    className={`w-full rounded-xl border text-sm text-slate-800 placeholder-slate-300 transition-all focus:outline-none focus:ring-2
                      ${field.type === "number" ? "pl-7 pr-3 py-2.5" : "px-3 py-2.5"}
                      ${isEdit && field.key === "codigo"
                        ? "bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed"
                        : errors[field.key]
                        ? "border-red-300 bg-red-50 focus:ring-red-200 focus:border-red-400"
                        : "border-blue-200 bg-white focus:ring-blue-200 focus:border-blue-400 hover:border-blue-300"
                      }`}
                  />
                  {isEdit && field.key === "codigo" && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2">
                      <svg className="w-3.5 h-3.5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                      </svg>
                    </span>
                  )}
                </div>
                {errors[field.key] && (
                  <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                    <svg className="w-3 h-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/></svg>
                    Campo requerido
                  </p>
                )}
              </div>
            ))}
          </div>

          {/* Live margin preview */}
          {form.costo_referencia && form.precio_publico && parseFloat(form.precio_publico) > 0 && (() => {
            const m = ((parseFloat(form.precio_publico) - parseFloat(form.costo_referencia)) / parseFloat(form.precio_publico)) * 100;
            const color = m >= 40 ? "border-emerald-200 bg-emerald-50 text-emerald-700" : m >= 20 ? "border-amber-200 bg-amber-50 text-amber-700" : "border-red-200 bg-red-50 text-red-600";
            return (
              <div className={`mt-4 rounded-xl border px-4 py-2.5 flex items-center justify-between ${color}`}>
                <span className="text-xs font-semibold">Vista previa del margen bruto</span>
                <span className="text-sm font-bold tabular-nums">{m.toFixed(1)}%</span>
              </div>
            );
          })()}
        </div>

        {/* Footer / Actions */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-600 border border-slate-200 bg-white hover:bg-slate-100 active:scale-95 transition-all"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            className={`px-6 py-2.5 rounded-xl text-sm font-semibold text-white shadow-sm active:scale-95 transition-all flex items-center gap-2
              ${isEdit ? "bg-blue-500 hover:bg-blue-600" : "bg-emerald-500 hover:bg-emerald-600"}`}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
            </svg>
            {isEdit ? "Guardar cambios" : "Crear producto"}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes modalIn {
          from { opacity: 0; transform: scale(0.94) translateY(12px); }
          to   { opacity: 1; transform: scale(1)    translateY(0);    }
        }
      `}</style>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   MAIN COMPONENT — VistaInventario
═══════════════════════════════════════════════════════════════ */
export default function VistaInventario({ products: initialProducts = SAMPLE_DATA }) {
  const [products, setProducts] = useState(initialProducts);
  const [query, setQuery]       = useState("");
  const [sortKey, setSortKey]   = useState("nombre");
  const [sortDir, setSortDir]   = useState("asc");
  const [selected, setSelected] = useState(null);
  const [catFilter, setCatFilter] = useState("Todos");

  /* Modal state */
  const [modalOpen, setModalOpen]   = useState(false);
  const [modalMode, setModalMode]   = useState("create"); // "create" | "edit"
  const [modalData, setModalData]   = useState(null);

  /* Toast notification */
  const [toast, setToast] = useState(null);
  const showToast = (msg, type = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const openCreate = () => { setModalMode("create"); setModalData(null); setModalOpen(true); };
  const openEdit   = (product) => { setModalMode("edit"); setModalData(product); setModalOpen(true); };
  const closeModal = () => setModalOpen(false);

  const handleSave = (data, mode) => {
    if (mode === "create") {
      const exists = products.some((p) => p.codigo === data.codigo);
      if (exists) { alert(`Ya existe un producto con el código "${data.codigo}".`); return; }
      setProducts((prev) => [...prev, data]);
      showToast(`Producto "${data.nombre}" creado correctamente.`);
    } else {
      setProducts((prev) => prev.map((p) => p.codigo === data.codigo ? data : p));
      showToast(`Producto "${data.nombre}" actualizado.`);
    }
    closeModal();
    setSelected(data.codigo);
  };

  const categories = useMemo(() => {
    const cats = [...new Set(products.map((p) => p.categoria))];
    return ["Todos", ...cats.sort()];
  }, [products]);

  const handleSort = (key) => {
    if (!COLUMNS.find((c) => c.key === key)?.sortable) return;
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("asc"); }
  };

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    return products
      .filter((p) => {
        const matchSearch = !q || p.nombre.toLowerCase().includes(q) || p.codigo.toLowerCase().includes(q) || p.laboratorio.toLowerCase().includes(q);
        const matchCat = catFilter === "Todos" || p.categoria === catFilter;
        return matchSearch && matchCat;
      })
      .sort((a, b) => {
        let av = a[sortKey] ?? ""; let bv = b[sortKey] ?? "";
        if (typeof av === "string") av = av.toLowerCase();
        if (typeof bv === "string") bv = bv.toLowerCase();
        return av < bv ? (sortDir === "asc" ? -1 : 1) : av > bv ? (sortDir === "asc" ? 1 : -1) : 0;
      });
  }, [products, query, sortKey, sortDir, catFilter]);

  const selectedProduct = selected ? products.find((p) => p.codigo === selected) : null;

  return (
    <div className="min-h-screen font-sans" style={{ background: "linear-gradient(135deg,#f0f7ff 0%,#e8f5f0 50%,#f5fbff 100%)", fontFamily: "'DM Sans','Segoe UI',system-ui,sans-serif" }}>

      {/* ── Toast ── */}
      {toast && (
        <div className={`fixed top-5 right-5 z-[60] flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg text-sm font-semibold border transition-all
          ${toast.type === "success" ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-red-50 border-red-200 text-red-700"}`}
          style={{ animation: "modalIn 0.2s ease both" }}
        >
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
          </svg>
          {toast.msg}
        </div>
      )}

      {/* ── Modal ── */}
      <ProductoModal isOpen={modalOpen} mode={modalMode} initialData={modalData} onClose={closeModal} onSave={handleSave}/>

      {/* ── Header ── */}
      <header className="bg-white border-b border-blue-100 shadow-sm sticky top-0 z-40">
        <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-teal-400 flex items-center justify-center shadow">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18"/>
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-800 leading-none">Inventario de Productos</h1>
              <p className="text-xs text-slate-400 mt-0.5">Clínica Veterinaria · POS System</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-medium bg-blue-50 text-blue-600 border border-blue-100 rounded-full px-3 py-1 hidden sm:inline-flex">
              {filtered.length} de {products.length} productos
            </span>
            {/* ── Nuevo Producto CTA ── */}
            <button
              onClick={openCreate}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-white shadow-md active:scale-95 transition-all"
              style={{ background: "linear-gradient(135deg, #10b981, #0ea5e9)" }}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4"/>
              </svg>
              <span className="hidden sm:inline">Nuevo Producto</span>
              <span className="sm:hidden">Nuevo</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-screen-2xl mx-auto px-6 py-6 space-y-4">

        {/* ── Search + Category filters ── */}
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
          <div className="relative flex-1 max-w-md">
            <svg className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-blue-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar por nombre, código o laboratorio…"
              className="w-full pl-10 pr-10 py-2.5 text-sm bg-white border border-blue-200 rounded-xl shadow-sm placeholder-slate-400 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 transition"
            />
            {query && (
              <button onClick={() => setQuery("")} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button key={cat} onClick={() => setCatFilter(cat)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${catFilter === cat ? "bg-blue-500 text-white border-blue-500 shadow-sm" : "bg-white text-slate-500 border-slate-200 hover:border-blue-300 hover:text-blue-500"}`}>
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* ── Table ── */}
        <div className="bg-white rounded-2xl shadow-sm border border-blue-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-blue-100" style={{ background: "linear-gradient(90deg,#f0f7ff,#edfaf4)" }}>
                  {COLUMNS.map((col) => (
                    <th key={col.key} onClick={() => handleSort(col.key)}
                      className={`px-4 py-3.5 text-left text-xs font-bold uppercase tracking-wider text-slate-500 select-none whitespace-nowrap ${col.sortable ? "cursor-pointer hover:text-blue-600 transition-colors" : ""}`}>
                      {col.label}
                      {col.sortable && <SortIcon direction={sortKey === col.key ? sortDir : null}/>}
                    </th>
                  ))}
                  <th className="px-4 py-3.5 text-right text-xs font-bold uppercase tracking-wider text-slate-500 whitespace-nowrap">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-16 text-center">
                      <div className="flex flex-col items-center gap-3 text-slate-400">
                        <svg className="w-10 h-10 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        <p className="text-sm font-medium">Sin resultados para <span className="text-blue-400">"{query}"</span></p>
                        <button onClick={() => { setQuery(""); setCatFilter("Todos"); }} className="text-xs text-blue-500 hover:underline">Limpiar filtros</button>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filtered.map((product, idx) => {
                    const isSelected = selected === product.codigo;
                    return (
                      <tr key={product.codigo} onClick={() => setSelected(isSelected ? null : product.codigo)}
                        className={`group transition-all duration-150 cursor-pointer ${isSelected ? "bg-blue-50" : idx % 2 === 0 ? "bg-white hover:bg-slate-50" : "bg-slate-50/50 hover:bg-blue-50/40"}`}
                        style={{ borderLeft: isSelected ? "4px solid #3b82f6" : "4px solid transparent" }}>
                        <td className="px-4 py-3.5 whitespace-nowrap">
                          <span className="font-mono text-xs font-semibold text-teal-700 bg-teal-50 px-2 py-1 rounded-lg tracking-wide">{product.codigo}</span>
                        </td>
                        <td className="px-4 py-3.5 min-w-[220px]">
                          <span className="font-semibold text-slate-800 text-sm leading-snug line-clamp-2 group-hover:text-blue-700 transition-colors">{product.nombre}</span>
                        </td>
                        <td className="px-4 py-3.5 whitespace-nowrap"><CategoryBadge categoria={product.categoria}/></td>
                        <td className="px-4 py-3.5 whitespace-nowrap">
                          <span className="text-xs text-slate-500 italic capitalize">{product.laboratorio === "- Sin Departamento -" ? <span className="text-slate-300">—</span> : product.laboratorio}</span>
                        </td>
                        <td className="px-4 py-3.5 whitespace-nowrap tabular-nums text-slate-500 text-xs font-medium">{fmt(product.costo_referencia)}</td>
                        <td className="px-4 py-3.5 whitespace-nowrap"><span className="tabular-nums font-bold text-slate-800 text-sm">{fmt(product.precio_publico)}</span></td>
                        <td className="px-4 py-3.5 whitespace-nowrap tabular-nums text-sm font-semibold text-blue-600">
                          {product.precio_mayoreo > 0 ? fmt(product.precio_mayoreo) : <span className="text-slate-300 text-xs font-normal">N/A</span>}
                        </td>
                        <td className="px-4 py-3.5 whitespace-nowrap text-center">
                          <MarginBadge costo={product.costo_referencia} precio={product.precio_publico}/>
                        </td>
                        <td className="px-4 py-3.5 whitespace-nowrap text-right">
                          <button onClick={(e) => { e.stopPropagation(); }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-500 text-white hover:bg-blue-600 active:scale-95 transition-all shadow-sm">
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4"/></svg>
                            Agregar
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Footer stats */}
          <div className="border-t border-blue-50 px-5 py-3 flex flex-wrap gap-4 items-center justify-between bg-gradient-to-r from-slate-50 to-blue-50/30">
            <p className="text-xs text-slate-400">
              Mostrando <span className="font-semibold text-slate-600">{filtered.length}</span> producto{filtered.length !== 1 && "s"}
              {query && <> · filtrado por <span className="font-semibold text-blue-500">"{query}"</span></>}
            </p>
            <div className="flex items-center gap-4 text-xs text-slate-400">
              {[["bg-emerald-400","Margen ≥40%"],["bg-amber-400","Margen 20–39%"],["bg-red-400","Margen <20%"]].map(([bg, label]) => (
                <span key={label} className="flex items-center gap-1.5"><span className={`w-2.5 h-2.5 rounded-full ${bg} inline-block`}/>{label}</span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Detail panel ── */}
        {selectedProduct && (() => {
          const p = selectedProduct;
          const margin = ((p.precio_publico - p.costo_referencia) / p.precio_publico) * 100;
          return (
            <div className="bg-white rounded-2xl border border-blue-200 shadow-md p-5">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-base font-bold text-slate-800">{p.nombre}</h2>
                  <p className="text-xs text-slate-400 mt-0.5 font-mono">{p.codigo} · <span className="capitalize">{p.laboratorio}</span></p>
                </div>
                <div className="flex items-center gap-2">
                  {/* ── Edit button ── */}
                  <button
                    onClick={() => openEdit(p)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold border border-blue-200 text-blue-600 bg-blue-50 hover:bg-blue-100 active:scale-95 transition-all"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                    Editar
                  </button>
                  <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-1.5 rounded-lg transition">
                    <svg className="w-4.5 h-4.5 w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {[
                  { label: "Precio Público",   value: fmt(p.precio_publico),   accent: "text-slate-800",  bg: "bg-slate-50"  },
                  { label: "Precio Mayoreo",    value: p.precio_mayoreo > 0 ? fmt(p.precio_mayoreo) : "N/A", accent: "text-blue-600", bg: "bg-blue-50" },
                  { label: "Costo Referencia",  value: fmt(p.costo_referencia), accent: "text-slate-500",  bg: "bg-slate-50"  },
                  { label: "Margen Bruto",      value: `${margin.toFixed(1)}%`, accent: margin >= 40 ? "text-emerald-600" : margin >= 20 ? "text-amber-500" : "text-red-500", bg: "bg-slate-50" },
                ].map(item => (
                  <div key={item.label} className={`${item.bg} rounded-xl px-4 py-3`}>
                    <p className="text-xs text-slate-400 mb-1">{item.label}</p>
                    <p className={`text-lg font-bold tabular-nums ${item.accent}`}>{item.value}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex gap-3">
                <button className="flex-1 py-2.5 rounded-xl bg-blue-500 text-white text-sm font-semibold hover:bg-blue-600 active:scale-95 transition-all shadow-sm">
                  + Agregar al carrito
                </button>
                <button className="px-4 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-sm font-semibold hover:bg-slate-50 transition-all">
                  Ver historial
                </button>
              </div>
            </div>
          );
        })()}
      </main>

      <style>{`
        @keyframes modalIn {
          from { opacity:0; transform:scale(0.94) translateY(12px); }
          to   { opacity:1; transform:scale(1)    translateY(0);    }
        }
      `}</style>
    </div>
  );
}