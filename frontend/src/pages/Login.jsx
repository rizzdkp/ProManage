import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { MessageCircle, Mail, Lock, ArrowRight, Eye, EyeOff, Phone } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';

const Login = () => {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [emailForm, setEmailForm] = useState({ email: '', password: '' });
  const [waPhone, setWaPhone] = useState('');

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    if (!emailForm.email || !emailForm.password) {
      toast.error('Mohon isi semua field');
      return;
    }
    const result = await login(emailForm.email, emailForm.password);
    if (result.success) {
      toast.success('Berhasil masuk!');
      navigate('/');
    } else {
      toast.error(result.error || 'Kredensial tidak valid');
    }
  };

  const handleWaLogin = async (e) => {
    e.preventDefault();
    if (!waPhone) {
      toast.error('Mohon isi nomor WhatsApp');
      return;
    }
    const result = await login(waPhone, 'password123');
    if (result.success) {
      toast.success('Berhasil masuk via WhatsApp!');
      navigate('/');
    } else {
      toast.error(result.error);
    }
  };

  return (
    <div className="min-h-screen flex" style={{ background: '#F9FAFB' }}>
      {/* Left Panel */}
      <div className="hidden lg:flex lg:w-1/2 items-center justify-center relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #0A2540 0%, #1E3A5F 100%)' }}>
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 rounded-full" style={{ background: '#D4AF77', filter: 'blur(100px)' }} />
          <div className="absolute bottom-20 right-20 w-96 h-96 rounded-full" style={{ background: '#D4AF77', filter: 'blur(120px)' }} />
        </div>
        <div className="relative z-10 max-w-md px-8">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-lg font-bold" style={{ background: '#D4AF77', color: '#0A2540' }}>
              PM
            </div>
            <span className="text-2xl font-bold text-white">ProManage</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
            Kelola Proyek<br />Lebih Efisien
          </h1>
          <p className="text-white/70 text-lg leading-relaxed">
            Platform manajemen proyek terpadu dengan integrasi WhatsApp untuk kolaborasi tim yang lebih produktif.
          </p>
          <div className="mt-10 space-y-4">
            {['Manajemen tugas & subtask', 'Notifikasi real-time', 'Integrasi WhatsApp'].map((feature, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: 'rgba(212, 175, 119, 0.2)' }}>
                  <div className="w-2 h-2 rounded-full" style={{ background: '#D4AF77' }} />
                </div>
                <span className="text-white/80 text-sm">{feature}</span>
              </div>
            ))}
          </div>
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
          {/* Mobile Logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm" style={{ background: '#0A2540' }}>
              PM
            </div>
            <span className="text-xl font-bold" style={{ color: '#0A2540' }}>ProManage</span>
          </div>

          <h2 className="text-2xl font-bold mb-1" style={{ color: '#111827' }}>Selamat Datang</h2>
          <p className="text-[#6B7280] mb-8">Masuk ke akun Anda untuk melanjutkan</p>

          <Tabs defaultValue="whatsapp" className="w-full">
            <TabsList className="w-full mb-6 h-12 p-1 rounded-xl" style={{ background: '#F3F4F6' }}>
              <TabsTrigger value="whatsapp" className="flex-1 rounded-lg h-full gap-2 text-sm font-medium data-[state=active]:shadow-sm" style={{ }}>
                <MessageCircle size={16} /> WhatsApp
              </TabsTrigger>
              <TabsTrigger value="email" className="flex-1 rounded-lg h-full gap-2 text-sm font-medium data-[state=active]:shadow-sm">
                <Mail size={16} /> Email
              </TabsTrigger>
            </TabsList>

            <TabsContent value="whatsapp">
              <form onSubmit={handleWaLogin} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="wa-phone" className="text-sm font-medium" style={{ color: '#111827' }}>Nomor WhatsApp</Label>
                  <div className="relative">
                    <Phone size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                    <Input
                      id="wa-phone"
                      placeholder="628xxxxxxxxxx"
                      value={waPhone}
                      onChange={e => setWaPhone(e.target.value)}
                      className="pl-10 h-12 rounded-xl border-[#E5E7EB] focus:border-[#0A2540] focus:ring-[#0A2540]"
                    />
                  </div>
                  <p className="text-xs text-[#9CA3AF]">Gunakan format internasional (628xxx)</p>
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12 rounded-xl text-sm font-semibold transition-all duration-200 hover:shadow-lg"
                  style={{ background: '#0A2540', color: 'white' }}
                  onMouseEnter={e => e.currentTarget.style.background = '#1E3A5F'}
                  onMouseLeave={e => e.currentTarget.style.background = '#0A2540'}
                >
                  {loading ? 'Memproses...' : 'Masuk via WhatsApp'}
                  <ArrowRight size={16} className="ml-2" />
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="email">
              <form onSubmit={handleEmailLogin} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium" style={{ color: '#111827' }}>Email</Label>
                  <div className="relative">
                    <Mail size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="email@contoh.com"
                      value={emailForm.email}
                      onChange={e => setEmailForm(p => ({ ...p, email: e.target.value }))}
                      className="pl-10 h-12 rounded-xl border-[#E5E7EB] focus:border-[#0A2540] focus:ring-[#0A2540]"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium" style={{ color: '#111827' }}>Password</Label>
                  <div className="relative">
                    <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Masukkan password"
                      value={emailForm.password}
                      onChange={e => setEmailForm(p => ({ ...p, password: e.target.value }))}
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

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12 rounded-xl text-sm font-semibold transition-all duration-200 hover:shadow-lg"
                  style={{ background: '#0A2540', color: 'white' }}
                  onMouseEnter={e => e.currentTarget.style.background = '#1E3A5F'}
                  onMouseLeave={e => e.currentTarget.style.background = '#0A2540'}
                >
                  {loading ? 'Memproses...' : 'Masuk'}
                  <ArrowRight size={16} className="ml-2" />
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          <p className="text-center text-sm text-[#6B7280] mt-8">
            Belum punya akun?{' '}
            <Link to="/register" className="font-semibold hover:underline" style={{ color: '#0A2540' }}>Daftar Sekarang</Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default Login;
