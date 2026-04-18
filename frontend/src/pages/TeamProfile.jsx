import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  User, Mail, Phone, Shield, Save, Lock, Trash2, Search
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../components/ui/alert-dialog';
import { useAuth } from '../context/AuthContext';
import { usersAPI } from '../lib/api';
import { toast } from 'sonner';

const roleColors = {
  'Manager': { bg: '#EFF6FF', text: '#1D4ED8' },
  'Admin': { bg: '#F5F3FF', text: '#7C3AED' },
  'Team Lead': { bg: '#FEF3C7', text: '#92400E' },
  'Anggota Tim': { bg: '#ECFDF5', text: '#0F766E' },
};

const TeamProfile = () => {
  const { user, updateProfile, canManage } = useAuth();
  const [profileForm, setProfileForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || '',
  });
  const [passwordForm, setPasswordForm] = useState({ current: '', newPass: '', confirm: '' });
  const [deleteUserId, setDeleteUserId] = useState(null);
  const [searchMember, setSearchMember] = useState('');
  const [allUsers, setAllUsers] = useState([]);
  const [savingProfile, setSavingProfile] = useState(false);

  useEffect(() => {
    usersAPI.getAll().then(r => setAllUsers(r.data || [])).catch(() => {});
  }, []);

  const filteredUsers = allUsers.filter(u =>
    !u.deletedAt && (
      u.name.toLowerCase().includes(searchMember.toLowerCase()) ||
      (u.email || '').toLowerCase().includes(searchMember.toLowerCase())
    )
  );

  const groupedUsers = {
    'Manager': filteredUsers.filter(u => u.role === 'Manager'),
    'Admin': filteredUsers.filter(u => u.role === 'Admin'),
    'Team Lead': filteredUsers.filter(u => u.role === 'Team Lead'),
    'Anggota Tim': filteredUsers.filter(u => u.role === 'Anggota Tim'),
  };

  const handleSaveProfile = async () => {
    setSavingProfile(true);
    try {
      const res = await usersAPI.update(user.id, profileForm);
      updateProfile(res.data);
      toast.success('Profil berhasil diperbarui!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal memperbarui profil');
    }
    setSavingProfile(false);
  };

  const handleResetPassword = async () => {
    if (!passwordForm.current || !passwordForm.newPass || !passwordForm.confirm) {
      toast.error('Semua field harus diisi');
      return;
    }
    if (passwordForm.newPass !== passwordForm.confirm) {
      toast.error('Password baru tidak cocok');
      return;
    }
    try {
      await usersAPI.changePassword(user.id, { currentPassword: passwordForm.current, newPassword: passwordForm.newPass });
      toast.success('Password berhasil diubah!');
      setPasswordForm({ current: '', newPass: '', confirm: '' });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal mengubah password');
    }
  };

  const handleDeleteUser = async () => {
    try {
      await usersAPI.delete(deleteUserId);
      toast.success('Akun berhasil dihapus');
      setDeleteUserId(null);
      usersAPI.getAll().then(r => setAllUsers(r.data || [])).catch(() => {});
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal menghapus akun');
    }
  };

  const getInitials = (name) => name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || '?';

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold" style={{ color: '#111827' }}>Tim & Profil</h1>
        <p className="text-[#6B7280] text-sm mt-1">Kelola profil dan lihat anggota tim</p>
      </motion.div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="h-11 p-1 rounded-xl" style={{ background: '#F3F4F6' }}>
          <TabsTrigger value="profile" className="rounded-lg px-4 h-full text-sm font-medium data-[state=active]:shadow-sm">
            Profil Saya
          </TabsTrigger>
          <TabsTrigger value="team" className="rounded-lg px-4 h-full text-sm font-medium data-[state=active]:shadow-sm">
            Anggota Tim
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Edit Profile */}
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl border border-[#E5E7EB] p-6">
              <h3 className="font-semibold text-[#111827] mb-5">Edit Profil</h3>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-xl font-bold text-white" style={{ background: '#D4AF77' }}>
                  {getInitials(user?.name)}
                </div>
                <div>
                  <p className="font-semibold text-[#111827]">{user?.name}</p>
                  <span className="text-xs font-medium px-2.5 py-0.5 rounded-full" style={{ background: roleColors[user?.role]?.bg, color: roleColors[user?.role]?.text }}>
                    {user?.role}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Nama Lengkap</Label>
                  <div className="relative">
                    <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                    <Input value={profileForm.name} onChange={e => setProfileForm(p => ({ ...p, name: e.target.value }))} className="pl-10 h-11 rounded-xl" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Email</Label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                    <Input value={profileForm.email} onChange={e => setProfileForm(p => ({ ...p, email: e.target.value }))} className="pl-10 h-11 rounded-xl" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Nomor WhatsApp</Label>
                  <div className="relative">
                    <Phone size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                    <Input value={profileForm.phone} onChange={e => setProfileForm(p => ({ ...p, phone: e.target.value }))} className="pl-10 h-11 rounded-xl" />
                  </div>
                </div>
                <Button onClick={handleSaveProfile} disabled={savingProfile} className="rounded-xl gap-2 font-semibold" style={{ background: '#0A2540', color: 'white' }}>
                  <Save size={16} /> {savingProfile ? 'Menyimpan...' : 'Simpan Perubahan'}
                </Button>
              </div>
            </motion.div>

            {/* Reset Password */}
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white rounded-2xl border border-[#E5E7EB] p-6">
              <h3 className="font-semibold text-[#111827] mb-5">Ubah Password</h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Password Saat Ini</Label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                    <Input type="password" value={passwordForm.current} onChange={e => setPasswordForm(p => ({ ...p, current: e.target.value }))} className="pl-10 h-11 rounded-xl" placeholder="Password saat ini" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Password Baru</Label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                    <Input type="password" value={passwordForm.newPass} onChange={e => setPasswordForm(p => ({ ...p, newPass: e.target.value }))} className="pl-10 h-11 rounded-xl" placeholder="Password baru" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Konfirmasi Password Baru</Label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                    <Input type="password" value={passwordForm.confirm} onChange={e => setPasswordForm(p => ({ ...p, confirm: e.target.value }))} className="pl-10 h-11 rounded-xl" placeholder="Ulangi password baru" />
                  </div>
                </div>
                <Button onClick={handleResetPassword} variant="outline" className="rounded-xl gap-2 font-semibold border-[#0A2540] text-[#0A2540] hover:bg-[#0A2540] hover:text-white">
                  <Lock size={16} /> Ubah Password
                </Button>
              </div>
            </motion.div>
          </div>
        </TabsContent>

        {/* Team Tab */}
        <TabsContent value="team">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
            <div className="mb-4">
              <div className="relative max-w-md">
                <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
                <Input placeholder="Cari anggota..." value={searchMember} onChange={e => setSearchMember(e.target.value)} className="pl-10 h-11 rounded-xl" />
              </div>
            </div>

            <div className="space-y-6">
              {Object.entries(groupedUsers).map(([role, users]) => {
                if (users.length === 0) return null;
                const rc = roleColors[role];
                return (
                  <div key={role}>
                    <div className="flex items-center gap-2 mb-3">
                      <Shield size={16} style={{ color: rc.text }} />
                      <h3 className="font-semibold text-sm" style={{ color: rc.text }}>{role}</h3>
                      <span className="text-xs text-[#9CA3AF]">({users.length})</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {users.map(u => (
                        <div key={u.id} className="bg-white rounded-2xl border border-[#E5E7EB] p-4 flex items-center gap-3 hover:shadow-sm transition-shadow">
                          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold text-white" style={{ background: '#D4AF77' }}>
                            {getInitials(u.name)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm text-[#111827] truncate">{u.name}</p>
                            <p className="text-xs text-[#6B7280] truncate">{u.email || u.phone}</p>
                          </div>
                          {canManage && u.id !== user?.id && (
                            <Button variant="ghost" size="icon" className="text-[#E11D48] hover:bg-[#FEF2F2] flex-shrink-0" onClick={() => setDeleteUserId(u.id)}>
                              <Trash2 size={16} />
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </TabsContent>
      </Tabs>

      {/* Delete User Confirm */}
      <AlertDialog open={!!deleteUserId} onOpenChange={() => setDeleteUserId(null)}>
        <AlertDialogContent className="rounded-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus Akun?</AlertDialogTitle>
            <AlertDialogDescription>Akun ini akan dihapus. Anda yakin ingin melanjutkan?</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-xl">Batal</AlertDialogCancel>
            <AlertDialogAction className="rounded-xl bg-[#E11D48] hover:bg-[#BE123C]" onClick={handleDeleteUser}>Hapus</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default TeamProfile;
