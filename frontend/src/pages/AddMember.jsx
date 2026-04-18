import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  UserPlus, User, Phone, Mail, Shield, ArrowLeft
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

const AddMember = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '',
    phone: '',
    email: '',
    role: '',
    password: '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.name || !form.phone || !form.role || !form.password) {
      toast.error('Nama, Nomor WA, Role, dan Password wajib diisi');
      return;
    }
    toast.success(`Anggota "${form.name}" berhasil ditambahkan! (Mock)`);
    setForm({ name: '', phone: '', email: '', role: '', password: '' });
  };

  return (
    <div className="max-w-lg mx-auto">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-[#6B7280] hover:text-[#111827] mb-4 transition-colors">
          <ArrowLeft size={16} /> Kembali
        </button>

        <h1 className="text-2xl font-bold mb-1" style={{ color: '#111827' }}>Tambah Anggota</h1>
        <p className="text-[#6B7280] text-sm mb-6">Tambahkan anggota baru ke dalam tim</p>

        <div className="bg-white rounded-2xl border border-[#E5E7EB] p-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label className="text-sm font-medium">
                Nama Lengkap <span className="text-[#E11D48]">*</span>
              </Label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                <Input placeholder="Nama lengkap" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} className="pl-10 h-11 rounded-xl" />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium">
                Nomor WhatsApp <span className="text-[#E11D48]">*</span>
              </Label>
              <div className="relative">
                <Phone size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                <Input placeholder="628xxxxxxxxxx" value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))} className="pl-10 h-11 rounded-xl" />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium">
                Email <span className="text-[#9CA3AF] font-normal">(Opsional)</span>
              </Label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                <Input type="email" placeholder="email@contoh.com" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} className="pl-10 h-11 rounded-xl" />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium">
                Role <span className="text-[#E11D48]">*</span>
              </Label>
              <Select value={form.role} onValueChange={v => setForm(p => ({ ...p, role: v }))}>
                <SelectTrigger className="h-11 rounded-xl">
                  <div className="flex items-center gap-2">
                    <Shield size={16} className="text-[#9CA3AF]" />
                    <SelectValue placeholder="Pilih role" />
                  </div>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Admin">Admin</SelectItem>
                  <SelectItem value="Team Lead">Team Lead</SelectItem>
                  <SelectItem value="Anggota Tim">Anggota Tim</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium">
                Password <span className="text-[#E11D48]">*</span>
              </Label>
              <Input type="password" placeholder="Password untuk akun baru" value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} className="h-11 rounded-xl" />
            </div>

            <Button
              type="submit"
              className="w-full h-11 rounded-xl font-semibold gap-2 transition-all duration-200 hover:shadow-lg"
              style={{ background: '#0A2540', color: 'white' }}
              onMouseEnter={e => e.currentTarget.style.background = '#1E3A5F'}
              onMouseLeave={e => e.currentTarget.style.background = '#0A2540'}
            >
              <UserPlus size={16} /> Tambah Anggota
            </Button>
          </form>
        </div>
      </motion.div>
    </div>
  );
};

export default AddMember;
