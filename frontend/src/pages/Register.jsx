import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { User, Phone, Mail, Lock, ArrowRight, Eye, EyeOff, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const Register = () => {
  const { register, loading } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({
    name: '',
    phone: '',
    password: '',
    email: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.phone || !form.password) {
      toast.error('Nama, Nomor WA, dan Password wajib diisi');
      return;
    }
    if (form.password.length < 6) {
      toast.error('Password minimal 6 karakter');
      return;
    }
    const result = await register({ name: form.name, phone: form.phone, password: form.password, email: form.email || undefined });
    if (result.success) {
      toast.success('Registrasi berhasil! Selamat datang.');
      navigate('/');
    } else {
      toast.error(result.error || 'Gagal mendaftar');
    }
  };

  const updateField = (field, value) => {
    setForm(p => ({ ...p, [field]: value }));
  };

  return (
    <div className="min-h-screen flex" style={{ background: '#F9FAFB' }}>
      {/* Left Panel */}
      <div className="hidden lg:flex lg:w-1/2 items-center justify-center relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #0A2540 0%, #1E3A5F 100%)' }}>
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 right-20 w-72 h-72 rounded-full" style={{ background: '#D4AF77', filter: 'blur(100px)' }} />
          <div className="absolute bottom-40 left-10 w-96 h-96 rounded-full" style={{ background: '#D4AF77', filter: 'blur(120px)' }} />
        </div>
        <div className="relative z-10 max-w-md px-8">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-lg font-bold" style={{ background: '#D4AF77', color: '#0A2540' }}>
              PM
            </div>
            <span className="text-2xl font-bold text-white">ProManage</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
            Bergabung dengan<br />Tim Terbaik
          </h1>
          <p className="text-white/70 text-lg leading-relaxed">
            Daftarkan diri Anda dan mulai berkolaborasi dengan tim untuk menyelesaikan proyek secara efisien.
          </p>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="flex-1 flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <Link
            to="/login"
            className="inline-flex items-center gap-1 text-sm text-[#6B7280] hover:text-[#111827] mb-6 transition-colors"
          >
            <ArrowLeft size={16} /> Kembali ke Login
          </Link>

          {/* Mobile Logo */}
          <div className="flex items-center gap-3 mb-6 lg:hidden">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm" style={{ background: '#0A2540' }}>
              PM
            </div>
            <span className="text-xl font-bold" style={{ color: '#0A2540' }}>ProManage</span>
          </div>

          <h2 className="text-2xl font-bold mb-1" style={{ color: '#111827' }}>Buat Akun Baru</h2>
          <p className="text-[#6B7280] mb-8">Lengkapi data diri untuk mendaftar</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label className="text-sm font-medium" style={{ color: '#111827' }}>
                Nama Lengkap <span className="text-[#E11D48]">*</span>
              </Label>
              <div className="relative">
                <User size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                <Input
                  placeholder="Masukkan nama lengkap"
                  value={form.name}
                  onChange={e => updateField('name', e.target.value)}
                  className="pl-10 h-12 rounded-xl border-[#E5E7EB] focus:border-[#0A2540] focus:ring-[#0A2540]"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium" style={{ color: '#111827' }}>
                Nomor WhatsApp <span className="text-[#E11D48]">*</span>
              </Label>
              <div className="relative">
                <Phone size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                <Input
                  placeholder="628xxxxxxxxxx"
                  value={form.phone}
                  onChange={e => updateField('phone', e.target.value)}
                  className="pl-10 h-12 rounded-xl border-[#E5E7EB] focus:border-[#0A2540] focus:ring-[#0A2540]"
                />
              </div>
              <p className="text-xs text-[#9CA3AF]">Format internasional (628xxx)</p>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium" style={{ color: '#111827' }}>
                Password <span className="text-[#E11D48]">*</span>
              </Label>
              <div className="relative">
                <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Minimal 6 karakter"
                  value={form.password}
                  onChange={e => updateField('password', e.target.value)}
                  className="pl-10 pr-10 h-12 rounded-xl border-[#E5E7EB] focus:border-[#0A2540] focus:ring-[#0A2540]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#6B7280]"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium" style={{ color: '#111827' }}>
                Email <span className="text-[#9CA3AF] font-normal">(Opsional)</span>
              </Label>
              <div className="relative">
                <Mail size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                <Input
                  type="email"
                  placeholder="email@contoh.com"
                  value={form.email}
                  onChange={e => updateField('email', e.target.value)}
                  className="pl-10 h-12 rounded-xl border-[#E5E7EB] focus:border-[#0A2540] focus:ring-[#0A2540]"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 rounded-xl text-sm font-semibold transition-all duration-200 hover:shadow-lg"
              style={{ background: '#0A2540', color: 'white' }}
              onMouseEnter={e => e.currentTarget.style.background = '#1E3A5F'}
              onMouseLeave={e => e.currentTarget.style.background = '#0A2540'}
            >
              {loading ? 'Memproses...' : 'Daftar Sekarang'}
              <ArrowRight size={16} className="ml-2" />
            </Button>
          </form>

          <p className="text-center text-sm text-[#6B7280] mt-8">
            Sudah punya akun?{' '}
            <Link to="/login" className="font-semibold hover:underline" style={{ color: '#0A2540' }}>Masuk</Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default Register;
