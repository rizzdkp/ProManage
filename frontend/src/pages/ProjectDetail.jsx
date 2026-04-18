import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft, Calendar, Users as UsersIcon, Plus, Trash2, Edit3,
  ChevronDown, ChevronUp, Send, CheckCircle2, Circle, AlertTriangle,
  Clock, Filter, Search, MoreVertical, MessageSquare, ListChecks
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Checkbox } from '../components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../components/ui/alert-dialog';
import { mockProjects, mockTasks, mockSubtasks, mockComments, mockUsers, getUserById, getProjectTasks, getTaskSubtasks, getTaskComments, getProjectMembers } from '../data/mock';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const statusColors = {
  'Selesai': { bg: '#ECFDF5', text: '#0F766E', border: '#A7F3D0' },
  'Dikerjakan': { bg: '#FEF3C7', text: '#92400E', border: '#FDE68A' },
  'Belum Mulai': { bg: '#F3F4F6', text: '#6B7280', border: '#E5E7EB' },
};

const priorityColors = {
  'Tinggi': { bg: '#FEF2F2', text: '#E11D48' },
  'Sedang': { bg: '#FEF3C7', text: '#D97706' },
  'Rendah': { bg: '#ECFDF5', text: '#0F766E' },
};

const ProjectDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { canManage } = useAuth();
  const project = mockProjects.find(p => p.id === id);
  const tasks = getProjectTasks(id);
  const members = project ? getProjectMembers(project) : [];

  const [expandedTask, setExpandedTask] = useState(null);
  const [taskFilter, setTaskFilter] = useState('all');
  const [taskSearch, setTaskSearch] = useState('');
  const [showAddTask, setShowAddTask] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [taskForm, setTaskForm] = useState({ name: '', description: '', dueDate: '', priority: '', assignee: '' });

  const filteredTasks = useMemo(() => {
    return tasks.filter(t => {
      const matchSearch = t.name.toLowerCase().includes(taskSearch.toLowerCase());
      const matchFilter = taskFilter === 'all' || t.status === taskFilter;
      return matchSearch && matchFilter;
    });
  }, [tasks, taskSearch, taskFilter]);

  if (!project) {
    return (
      <div className="text-center py-20">
        <p className="text-[#6B7280]">Proyek tidak ditemukan</p>
        <Button variant="outline" onClick={() => navigate('/projects')} className="mt-4 rounded-xl">
          <ArrowLeft size={16} className="mr-2" /> Kembali
        </Button>
      </div>
    );
  }

  const getStatusColor = (status) => statusColors[status] || statusColors['Belum Mulai'];
  const getPriorityColor = (priority) => priorityColors[priority] || priorityColors['Sedang'];

  return (
    <div className="space-y-6">
      {/* Back + Header */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <button onClick={() => navigate('/projects')} className="flex items-center gap-1 text-sm text-[#6B7280] hover:text-[#111827] mb-4 transition-colors">
          <ArrowLeft size={16} /> Kembali ke Proyek
        </button>
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: '#111827' }}>{project.name}</h1>
            <p className="text-[#6B7280] text-sm mt-1 max-w-xl">{project.description}</p>
          </div>
          {canManage && (
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowDeleteConfirm(true)} className="rounded-xl gap-2 text-sm text-[#E11D48] border-[#E11D48]/30 hover:bg-[#FEF2F2] hover:text-[#E11D48]">
                <Trash2 size={16} /> Hapus
              </Button>
              <Button onClick={() => setShowAddTask(true)} className="rounded-xl gap-2 text-sm font-semibold" style={{ background: '#0A2540', color: 'white' }}>
                <Plus size={16} /> Tambah Tugas
              </Button>
            </div>
          )}
        </div>
      </motion.div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl border border-[#E5E7EB] p-4">
          <p className="text-xs text-[#6B7280] mb-1">Progress</p>
          <div className="flex items-center gap-3">
            <Progress value={project.progress} className="h-2.5 flex-1 rounded-full" />
            <span className="text-lg font-bold" style={{ color: '#0A2540' }}>{project.progress}%</span>
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-[#E5E7EB] p-4">
          <p className="text-xs text-[#6B7280] mb-1">Status</p>
          <span className="text-sm font-semibold px-3 py-1 rounded-full" style={{ background: getStatusColor(project.status === 'Aktif' ? 'Dikerjakan' : project.status).bg, color: getStatusColor(project.status === 'Aktif' ? 'Dikerjakan' : project.status).text }}>
            {project.status}
          </span>
        </div>
        <div className="bg-white rounded-2xl border border-[#E5E7EB] p-4">
          <p className="text-xs text-[#6B7280] mb-1">Periode</p>
          <div className="flex items-center gap-1.5 text-sm text-[#111827]">
            <Calendar size={14} className="text-[#6B7280]" />
            {new Date(project.startDate).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })} - {new Date(project.endDate).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })}
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-[#E5E7EB] p-4">
          <p className="text-xs text-[#6B7280] mb-1">Anggota</p>
          <div className="flex items-center gap-2">
            <div className="flex -space-x-2">
              {members.slice(0, 4).map(m => (
                <div key={m.id} className="w-7 h-7 rounded-full border-2 border-white flex items-center justify-center text-[8px] font-bold text-white" style={{ background: '#D4AF77' }}>
                  {m.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </div>
              ))}
            </div>
            <span className="text-sm text-[#6B7280]">{members.length} anggota</span>
          </div>
        </div>
      </div>

      {/* Task Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
          <Input placeholder="Cari tugas..." value={taskSearch} onChange={e => setTaskSearch(e.target.value)} className="pl-10 h-11 rounded-xl border-[#E5E7EB]" />
        </div>
        <Select value={taskFilter} onValueChange={setTaskFilter}>
          <SelectTrigger className="w-full sm:w-[180px] h-11 rounded-xl border-[#E5E7EB]">
            <Filter size={16} className="mr-2 text-[#9CA3AF]" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua Status</SelectItem>
            <SelectItem value="Belum Mulai">Belum Mulai</SelectItem>
            <SelectItem value="Dikerjakan">Dikerjakan</SelectItem>
            <SelectItem value="Selesai">Selesai</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Tasks List */}
      <div className="space-y-3">
        {filteredTasks.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-2xl border border-[#E5E7EB]">
            <ListChecks size={40} className="mx-auto mb-3 text-[#D1D5DB]" />
            <p className="text-[#6B7280]">Tidak ada tugas ditemukan</p>
          </div>
        ) : (
          filteredTasks.map(task => {
            const subtasks = getTaskSubtasks(task.id);
            const comments = getTaskComments(task.id);
            const assigneeUser = getUserById(task.assignee);
            const sc = getStatusColor(task.status);
            const pc = getPriorityColor(task.priority);
            const isExpanded = expandedTask === task.id;
            const doneSubtasks = subtasks.filter(s => s.isDone).length;

            return (
              <motion.div
                key={task.id}
                layout
                className="bg-white rounded-2xl border border-[#E5E7EB] overflow-hidden hover:shadow-sm transition-shadow"
              >
                <div
                  className="px-5 py-4 cursor-pointer flex items-center gap-4"
                  onClick={() => setExpandedTask(isExpanded ? null : task.id)}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <h4 className="font-medium text-[#111827]">{task.name}</h4>
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{ background: sc.bg, color: sc.text, border: `1px solid ${sc.border}` }}>
                        {task.status}
                      </span>
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{ background: pc.bg, color: pc.text }}>
                        {task.priority}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-[#6B7280]">
                      {assigneeUser && (
                        <span className="flex items-center gap-1">
                          <div className="w-4 h-4 rounded-full flex items-center justify-center text-[6px] font-bold text-white" style={{ background: '#D4AF77' }}>
                            {assigneeUser.name[0]}
                          </div>
                          {assigneeUser.name}
                        </span>
                      )}
                      <span className="flex items-center gap-1"><Calendar size={12} /> {new Date(task.dueDate).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })}</span>
                      {subtasks.length > 0 && <span className="flex items-center gap-1"><ListChecks size={12} /> {doneSubtasks}/{subtasks.length}</span>}
                      {comments.length > 0 && <span className="flex items-center gap-1"><MessageSquare size={12} /> {comments.length}</span>}
                    </div>
                  </div>
                  <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
                    <ChevronDown size={18} className="text-[#9CA3AF]" />
                  </motion.div>
                </div>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="px-5 pb-5 pt-1 border-t border-[#E5E7EB]">
                        <p className="text-sm text-[#6B7280] mb-4">{task.description}</p>

                        {/* Subtasks */}
                        {subtasks.length > 0 && (
                          <div className="mb-4">
                            <h5 className="text-xs font-semibold text-[#111827] uppercase tracking-wider mb-2">Subtask ({doneSubtasks}/{subtasks.length})</h5>
                            <div className="space-y-2">
                              {subtasks.map(sub => (
                                <div key={sub.id} className="flex items-center gap-2.5 text-sm">
                                  <Checkbox checked={sub.isDone} className="rounded" />
                                  <span className={sub.isDone ? 'line-through text-[#9CA3AF]' : 'text-[#374151]'}>{sub.title}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Comments */}
                        {comments.length > 0 && (
                          <div>
                            <h5 className="text-xs font-semibold text-[#111827] uppercase tracking-wider mb-2">Komentar ({comments.length})</h5>
                            <div className="space-y-3 mb-3">
                              {comments.map(c => (
                                <div key={c.id} className="flex gap-2.5">
                                  <div className="w-7 h-7 rounded-full flex items-center justify-center text-[8px] font-bold text-white flex-shrink-0" style={{ background: '#0A2540' }}>
                                    {c.actor.split(' ').map(n => n[0]).join('').slice(0, 2)}
                                  </div>
                                  <div className="flex-1 bg-[#F9FAFB] rounded-xl p-3">
                                    <div className="flex items-center gap-2 mb-1">
                                      <span className="text-xs font-semibold text-[#111827]">{c.actor}</span>
                                      <span className="text-[10px] text-[#9CA3AF]">{new Date(c.timestamp).toLocaleDateString('id-ID')}</span>
                                    </div>
                                    <p className="text-sm text-[#374151]">{c.message}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                            <div className="flex gap-2">
                              <Input placeholder="Tulis komentar..." value={newComment} onChange={e => setNewComment(e.target.value)} className="h-9 rounded-xl text-sm" />
                              <Button size="sm" className="rounded-xl h-9 px-3" style={{ background: '#0A2540', color: 'white' }} onClick={() => { toast.success('Komentar ditambahkan (Mock)'); setNewComment(''); }}>
                                <Send size={14} />
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })
        )}
      </div>

      {/* Add Task Modal */}
      <Dialog open={showAddTask} onOpenChange={setShowAddTask}>
        <DialogContent className="rounded-2xl max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold" style={{ color: '#111827' }}>Tambah Tugas Baru</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Nama Tugas</Label>
              <Input placeholder="Nama tugas" value={taskForm.name} onChange={e => setTaskForm(p => ({ ...p, name: e.target.value }))} className="h-11 rounded-xl" />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Deskripsi</Label>
              <Textarea placeholder="Deskripsi tugas..." value={taskForm.description} onChange={e => setTaskForm(p => ({ ...p, description: e.target.value }))} className="rounded-xl min-h-[80px]" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-sm font-medium">Deadline</Label>
                <Input type="date" value={taskForm.dueDate} onChange={e => setTaskForm(p => ({ ...p, dueDate: e.target.value }))} className="h-11 rounded-xl" />
              </div>
              <div className="space-y-2">
                <Label className="text-sm font-medium">Prioritas</Label>
                <Select value={taskForm.priority} onValueChange={v => setTaskForm(p => ({ ...p, priority: v }))}>
                  <SelectTrigger className="h-11 rounded-xl"><SelectValue placeholder="Pilih" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Tinggi">Tinggi</SelectItem>
                    <SelectItem value="Sedang">Sedang</SelectItem>
                    <SelectItem value="Rendah">Rendah</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Ditugaskan Ke</Label>
              <Select value={taskForm.assignee} onValueChange={v => setTaskForm(p => ({ ...p, assignee: v }))}>
                <SelectTrigger className="h-11 rounded-xl"><SelectValue placeholder="Pilih anggota" /></SelectTrigger>
                <SelectContent>
                  {members.map(m => <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddTask(false)} className="rounded-xl">Batal</Button>
            <Button onClick={() => { toast.success('Tugas ditambahkan (Mock)'); setShowAddTask(false); }} className="rounded-xl font-semibold" style={{ background: '#0A2540', color: 'white' }}>Tambah Tugas</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirm */}
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent className="rounded-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus Proyek?</AlertDialogTitle>
            <AlertDialogDescription>Proyek "{project.name}" akan dihapus (soft delete). Anda yakin ingin melanjutkan?</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-xl">Batal</AlertDialogCancel>
            <AlertDialogAction className="rounded-xl bg-[#E11D48] hover:bg-[#BE123C]" onClick={() => { toast.success('Proyek dihapus (Mock)'); navigate('/projects'); }}>Hapus</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default ProjectDetail;
