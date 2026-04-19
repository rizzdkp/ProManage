import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FolderKanban, CheckCircle2, Clock, Users, Plus,
  ArrowRight, Wifi, WifiOff, UserPlus
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { statsAPI, projectsAPI, whatsappAPI, usersAPI } from '../lib/api';
import { toast } from 'sonner';

const fadeIn = { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4 } };

const StatCard = ({ icon: Icon, label, value, color, bgColor }) => (
  <motion.div {...fadeIn} className="bg-white rounded-2xl p-5 border border-[#E5E7EB] hover:shadow-md transition-shadow duration-300">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-[#6B7280] mb-1">{label}</p>
        <p className="text-2xl font-bold" style={{ color: '#111827' }}>{value}</p>
      </div>
      <div className="w-11 h-11 rounded-xl flex items-center justify-center" style={{ background: bgColor }}>
        <Icon size={20} style={{ color }} />
      </div>
    </div>
  </motion.div>
);

const Dashboard = () => {
  const { user, canManage } = useAuth();
  const navigate = useNavigate();
  const [showNewProject, setShowNewProject] = useState(false);
  const [showAddMember, setShowAddMember] = useState(false);
  const [projectForm, setProjectForm] = useState({ name: '', description: '', startDate: '', endDate: '' });
  const [memberForm, setMemberForm] = useState({ name: '', phone: '', email: '', role: '', password: '' });

  const [stats, setStats] = useState({ totalProjects: 0, completedTasks: 0, inProgressTasks: 0, totalMembers: 0, totalTasks: 0, pendingTasks: 0 });
  const [projects, setProjects] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [waStatus, setWaStatus] = useState({ enabled: false, provider: '', connected: false, configured: false, lastPing: null, sessionState: null, needsQrScan: false });
  const [showWaQr, setShowWaQr] = useState(false);
  const [waQr, setWaQr] = useState(null);
  const [waQrLoading, setWaQrLoading] = useState(false);
  const [loadingCreate, setLoadingCreate] = useState(false);

  const loadWaStatus = async () => {
    try {
      const response = await whatsappAPI.getStatus();
      setWaStatus(response.data || {});
      return response.data || null;
    } catch {
      return null;
    }
  };

  const loadData = () => {
    statsAPI.get().then(r => setStats(r.data)).catch(() => {});
    projectsAPI.getAll().then(r => setProjects((r.data || []).filter(p => !p.deletedAt).slice(0, 4))).catch(() => {});
    loadWaStatus();
    usersAPI.getAll().then(r => setAllUsers(r.data || [])).catch(() => {});
  };

  useEffect(() => { loadData(); }, []);

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Selamat Pagi';
    if (h < 17) return 'Selamat Siang';
    return 'Selamat Malam';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Aktif': return { bg: '#ECFDF5', text: '#0F766E' };
      case 'Selesai': return { bg: '#EFF6FF', text: '#1D4ED8' };
      case 'Tertunda': return { bg: '#FEF3C7', text: '#92400E' };
      default: return { bg: '#F3F4F6', text: '#6B7280' };
    }
  };

  const getUserById = (id) => allUsers.find(u => u.id === id);
  const getInitials = (name) => name ? name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : '?';

  const refreshWaQr = async () => {
    setWaQrLoading(true);
    setWaQr(null);
    try {
      await whatsappAPI.connect();
      const status = await loadWaStatus();
      if (status?.connected) {
        toast.success('WhatsApp sudah terhubung');
        return;
      }
      const qrResponse = await whatsappAPI.getQr();
      setWaQr(qrResponse.data?.qr || null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal mengambil QR WhatsApp');
    } finally {
      setWaQrLoading(false);
    }
  };

  const openWaQrDialog = async () => {
    setShowWaQr(true);
    await refreshWaQr();
  };

  const verifyWaConnected = async () => {
    const status = await loadWaStatus();
    if (status?.connected) {
      toast.success('WhatsApp berhasil terhubung');
      setShowWaQr(false);
      setWaQr(null);
      return;
    }
    toast.error('Belum terhubung. Silakan scan QR lalu cek lagi.');
  };

  const disconnectWaSession = async () => {
    try {
      await whatsappAPI.logout();
      toast.success('Session WhatsApp diputus');
      setWaQr(null);
      await loadWaStatus();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal memutuskan session WhatsApp');
    }
  };

  const handleCreateProject = async () => {
    if (!projectForm.name || !projectForm.startDate || !projectForm.endDate) {
      toast.error('Nama, tanggal mulai, dan tanggal selesai wajib diisi');
      return;
    }
    setLoadingCreate(true);
    try {
      await projectsAPI.create(projectForm);
      toast.success('Proyek berhasil dibuat!');
      setShowNewProject(false);
      setProjectForm({ name: '', description: '', startDate: '', endDate: '' });
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal membuat proyek');
    }
    setLoadingCreate(false);
  };

  const handleAddMember = async () => {
    if (!memberForm.name || !memberForm.phone || !memberForm.role || !memberForm.password) {
      toast.error('Nama, Nomor WA, Role, dan Password wajib diisi');
      return;
    }
    setLoadingCreate(true);
    try {
      await usersAPI.create({
        name: memberForm.name,
        phone: memberForm.phone,
        email: memberForm.email || undefined,
        role: memberForm.role,
        password: memberForm.password,
      });
      toast.success('Anggota berhasil ditambahkan!');
      setShowAddMember(false);
      setMemberForm({ name: '', phone: '', email: '', role: '', password: '' });
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal menambah anggota');
    }
    setLoadingCreate(false);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div {...fadeIn} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: '#111827' }}>{greeting()}, {user?.name?.split(' ')[0]}!</h1>
          <p className="text-[#6B7280] text-sm mt-1">Berikut ringkasan aktivitas proyek Anda</p>
        </div>
        <div className="flex gap-2">
          {canManage && (
            <>
              <Button
                onClick={() => setShowAddMember(true)}
                variant="outline"
                className="rounded-xl h-10 gap-2 text-sm border-[#E5E7EB] hover:border-[#0A2540] hover:text-[#0A2540]"
              >
                <UserPlus size={16} /> Tambah Anggota
              </Button>
              <Button
                onClick={() => setShowNewProject(true)}
                className="rounded-xl h-10 gap-2 text-sm font-semibold hover:shadow-lg transition-all duration-200"
                style={{ background: '#0A2540', color: 'white' }}
                onMouseEnter={e => e.currentTarget.style.background = '#1E3A5F'}
                onMouseLeave={e => e.currentTarget.style.background = '#0A2540'}
              >
                <Plus size={16} /> Buat Proyek
              </Button>
            </>
          )}
        </div>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FolderKanban} label="Total Proyek" value={stats.totalProjects} color="#0A2540" bgColor="#EFF6FF" />
        <StatCard icon={CheckCircle2} label="Tugas Selesai" value={stats.completedTasks} color="#0F766E" bgColor="#ECFDF5" />
        <StatCard icon={Clock} label="Sedang Dikerjakan" value={stats.inProgressTasks} color="#D97706" bgColor="#FEF3C7" />
        <StatCard icon={Users} label="Total Anggota" value={stats.totalMembers} color="#7C3AED" bgColor="#F5F3FF" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Projects */}
        <motion.div {...fadeIn} className="lg:col-span-2 bg-white rounded-2xl border border-[#E5E7EB] overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-[#E5E7EB]">
            <h3 className="font-semibold text-[#111827]">Proyek Terbaru</h3>
            <Link to="/projects" className="text-sm font-medium flex items-center gap-1 hover:underline" style={{ color: '#0A2540' }}>
              Lihat Semua <ArrowRight size={14} />
            </Link>
          </div>
          <div className="divide-y divide-[#E5E7EB]">
            {projects.length === 0 ? (
              <div className="px-6 py-10 text-center text-[#9CA3AF] text-sm">Belum ada proyek</div>
            ) : projects.map(project => {
              const sc = getStatusColor(project.status);
              return (
                <div
                  key={project.id}
                  className="px-6 py-4 hover:bg-[#F9FAFB] cursor-pointer transition-colors"
                  onClick={() => navigate(`/projects/${project.id}`)}
                >
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-[#111827] truncate">{project.name}</h4>
                      <p className="text-xs text-[#6B7280] mt-0.5 truncate">{project.description}</p>
                    </div>
                    <span className="text-xs font-medium px-2.5 py-1 rounded-full flex-shrink-0" style={{ background: sc.bg, color: sc.text }}>
                      {project.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <Progress value={project.progress} className="h-2 rounded-full" />
                    </div>
                    <span className="text-xs font-medium text-[#6B7280]">{project.progress}%</span>
                    <div className="flex -space-x-2">
                      {(project.teamMembers || []).slice(0, 3).map(mid => {
                        const m = getUserById(mid);
                        return m ? (
                          <div key={mid} className="w-6 h-6 rounded-full border-2 border-white flex items-center justify-center text-[8px] font-bold text-white" style={{ background: '#D4AF77' }}>
                            {getInitials(m.name)}
                          </div>
                        ) : null;
                      })}
                      {(project.teamMembers || []).length > 3 && (
                        <div className="w-6 h-6 rounded-full border-2 border-white flex items-center justify-center text-[8px] font-bold bg-[#F3F4F6] text-[#6B7280]">
                          +{project.teamMembers.length - 3}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* WA Gateway */}
          <motion.div {...fadeIn} className="bg-white rounded-2xl border border-[#E5E7EB] p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-[#111827] text-sm">WhatsApp Gateway</h3>
              {waStatus.connected ? (
                <span className="flex items-center gap-1.5 text-xs font-medium" style={{ color: '#0F766E' }}>
                  <Wifi size={14} /> Terhubung
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-xs font-medium" style={{ color: '#E11D48' }}>
                  <WifiOff size={14} /> Terputus
                </span>
              )}
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-[#6B7280]">Provider</span>
                <span className="text-[#111827] font-medium capitalize">{waStatus.provider || '-'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#6B7280]">State Sesi</span>
                <span className="text-[#111827] font-medium">{waStatus.sessionState || '-'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#6B7280]">Status</span>
                <span className={`font-medium ${waStatus.connected ? 'text-[#0F766E]' : 'text-[#E11D48]'}`}>
                  {waStatus.connected ? 'Aktif' : 'Tidak Aktif'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#6B7280]">Terakhir Ping</span>
                <span className="text-[#111827]">{waStatus.lastPing ? new Date(waStatus.lastPing).toLocaleString('id-ID') : '-'}</span>
              </div>
              {canManage && waStatus.enabled && waStatus.provider === 'waha' && (
                <div className="grid grid-cols-1 gap-2 pt-2">
                  <Button
                    variant="outline"
                    className="rounded-xl h-9 text-xs"
                    onClick={openWaQrDialog}
                  >
                    Scan QR WhatsApp
                  </Button>
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      variant="outline"
                      className="rounded-xl h-9 text-xs"
                      onClick={loadWaStatus}
                    >
                      Refresh Status
                    </Button>
                    <Button
                      variant="outline"
                      className="rounded-xl h-9 text-xs"
                      onClick={disconnectWaSession}
                      disabled={!waStatus.connected}
                    >
                      Putuskan Session
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>

          {/* Quick Overview */}
          <motion.div {...fadeIn} className="bg-white rounded-2xl border border-[#E5E7EB] p-5">
            <h3 className="font-semibold text-[#111827] text-sm mb-4">Ringkasan Tugas</h3>
            <div className="space-y-3">
              {[
                { label: 'Selesai', value: stats.completedTasks, total: stats.totalTasks, color: '#0F766E' },
                { label: 'Dikerjakan', value: stats.inProgressTasks, total: stats.totalTasks, color: '#D97706' },
                { label: 'Belum Mulai', value: stats.pendingTasks, total: stats.totalTasks, color: '#6B7280' },
              ].map(item => (
                <div key={item.label}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-[#6B7280]">{item.label}</span>
                    <span className="font-medium" style={{ color: item.color }}>{item.value}/{item.total || 0}</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-[#F3F4F6]">
                    <div className="h-2 rounded-full transition-all duration-500" style={{ width: `${item.total ? (item.value / item.total) * 100 : 0}%`, background: item.color }} />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* WhatsApp QR Modal */}
      <Dialog open={showWaQr} onOpenChange={(open) => {
        setShowWaQr(open);
        if (!open) {
          setWaQr(null);
          setWaQrLoading(false);
        }
      }}>
        <DialogContent className="rounded-2xl max-w-md">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold" style={{ color: '#111827' }}>Hubungkan WhatsApp via QR</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <p className="text-sm text-[#6B7280]">
              Buka WhatsApp di HP Anda, pilih Perangkat Tertaut, lalu scan QR berikut.
            </p>
            <div className="rounded-xl border border-[#E5E7EB] bg-[#FAFAFA] p-3 flex items-center justify-center min-h-[280px]">
              {waStatus.connected ? (
                <div className="text-center">
                  <p className="text-sm font-medium text-[#0F766E]">WhatsApp sudah terhubung.</p>
                  <p className="text-xs text-[#6B7280] mt-1">Anda sudah bisa menerima notifikasi WA.</p>
                </div>
              ) : waQrLoading ? (
                <p className="text-sm text-[#6B7280]">Memuat QR...</p>
              ) : waQr?.imageDataUrl ? (
                <img src={waQr.imageDataUrl} alt="QR WhatsApp" className="w-64 h-64 object-contain" />
              ) : (
                <p className="text-sm text-[#6B7280] text-center">QR belum tersedia. Klik Refresh QR untuk mengambil QR terbaru.</p>
              )}
            </div>
            {waQr?.raw && !waQr?.imageDataUrl && (
              <p className="text-xs break-all text-[#6B7280]">QR raw: {waQr.raw}</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={refreshWaQr} className="rounded-xl" disabled={waQrLoading}>
              Refresh QR
            </Button>
            <Button onClick={verifyWaConnected} className="rounded-xl font-semibold" style={{ background: '#0A2540', color: 'white' }}>
              Saya Sudah Scan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Project Modal */}
      <Dialog open={showNewProject} onOpenChange={setShowNewProject}>
        <DialogContent className="rounded-2xl max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold" style={{ color: '#111827' }}>Buat Proyek Baru</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Nama Proyek</Label>
              <Input placeholder="Contoh: Website Redesign" value={projectForm.name} onChange={e => setProjectForm(p => ({ ...p, name: e.target.value }))} className="h-11 rounded-xl" />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Deskripsi</Label>
              <Textarea placeholder="Deskripsi singkat proyek..." value={projectForm.description} onChange={e => setProjectForm(p => ({ ...p, description: e.target.value }))} className="rounded-xl min-h-[80px]" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-sm font-medium">Tanggal Mulai</Label>
                <Input type="date" value={projectForm.startDate} onChange={e => setProjectForm(p => ({ ...p, startDate: e.target.value }))} className="h-11 rounded-xl" />
              </div>
              <div className="space-y-2">
                <Label className="text-sm font-medium">Tanggal Selesai</Label>
                <Input type="date" value={projectForm.endDate} onChange={e => setProjectForm(p => ({ ...p, endDate: e.target.value }))} className="h-11 rounded-xl" />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewProject(false)} className="rounded-xl">Batal</Button>
            <Button onClick={handleCreateProject} disabled={loadingCreate} className="rounded-xl font-semibold" style={{ background: '#0A2540', color: 'white' }}>
              {loadingCreate ? 'Memproses...' : 'Buat Proyek'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Member Modal */}
      <Dialog open={showAddMember} onOpenChange={setShowAddMember}>
        <DialogContent className="rounded-2xl max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold" style={{ color: '#111827' }}>Tambah Anggota Baru</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Nama Lengkap</Label>
              <Input placeholder="Nama lengkap" value={memberForm.name} onChange={e => setMemberForm(p => ({ ...p, name: e.target.value }))} className="h-11 rounded-xl" />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Nomor WhatsApp</Label>
              <Input placeholder="628xxxxxxxxxx" value={memberForm.phone} onChange={e => setMemberForm(p => ({ ...p, phone: e.target.value }))} className="h-11 rounded-xl" />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Email (Opsional)</Label>
              <Input placeholder="email@contoh.com" type="email" value={memberForm.email} onChange={e => setMemberForm(p => ({ ...p, email: e.target.value }))} className="h-11 rounded-xl" />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Role</Label>
              <Select value={memberForm.role} onValueChange={v => setMemberForm(p => ({ ...p, role: v }))}>
                <SelectTrigger className="h-11 rounded-xl"><SelectValue placeholder="Pilih role" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="Admin">Admin</SelectItem>
                  <SelectItem value="Team Lead">Team Lead</SelectItem>
                  <SelectItem value="Anggota Tim">Anggota Tim</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Password</Label>
              <Input type="password" placeholder="Password akun baru" value={memberForm.password} onChange={e => setMemberForm(p => ({ ...p, password: e.target.value }))} className="h-11 rounded-xl" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddMember(false)} className="rounded-xl">Batal</Button>
            <Button onClick={handleAddMember} disabled={loadingCreate} className="rounded-xl font-semibold" style={{ background: '#0A2540', color: 'white' }}>
              {loadingCreate ? 'Memproses...' : 'Tambah Anggota'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Dashboard;
