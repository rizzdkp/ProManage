import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Search, Filter, Plus, Calendar, Users as UsersIcon, ArrowRight, FolderKanban
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Progress } from '../components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { mockProjects, getUserById } from '../data/mock';
import { useAuth } from '../context/AuthContext';

const Projects = () => {
  const navigate = useNavigate();
  const { canManage } = useAuth();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredProjects = useMemo(() => {
    return mockProjects.filter(p => {
      if (p.deletedAt) return false;
      const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.description.toLowerCase().includes(search.toLowerCase());
      const matchStatus = statusFilter === 'all' || p.status === statusFilter;
      return matchSearch && matchStatus;
    });
  }, [search, statusFilter]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'Aktif': return { bg: '#ECFDF5', text: '#0F766E', dot: '#0F766E' };
      case 'Selesai': return { bg: '#EFF6FF', text: '#1D4ED8', dot: '#1D4ED8' };
      case 'Tertunda': return { bg: '#FEF3C7', text: '#92400E', dot: '#F59E0B' };
      default: return { bg: '#F3F4F6', text: '#6B7280', dot: '#6B7280' };
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold" style={{ color: '#111827' }}>Proyek</h1>
          <p className="text-[#6B7280] text-sm mt-1">Kelola semua proyek tim Anda</p>
        </div>
        {canManage && (
          <Button
            className="rounded-xl h-10 gap-2 text-sm font-semibold hover:shadow-lg transition-all duration-200"
            style={{ background: '#0A2540', color: 'white' }}
            onMouseEnter={e => e.currentTarget.style.background = '#1E3A5F'}
            onMouseLeave={e => e.currentTarget.style.background = '#0A2540'}
          >
            <Plus size={16} /> Buat Proyek
          </Button>
        )}
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="flex flex-col sm:flex-row gap-3"
      >
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
          <Input
            placeholder="Cari proyek..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-10 h-11 rounded-xl border-[#E5E7EB]"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[180px] h-11 rounded-xl border-[#E5E7EB]">
            <Filter size={16} className="mr-2 text-[#9CA3AF]" />
            <SelectValue placeholder="Filter Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Semua Status</SelectItem>
            <SelectItem value="Aktif">Aktif</SelectItem>
            <SelectItem value="Selesai">Selesai</SelectItem>
            <SelectItem value="Tertunda">Tertunda</SelectItem>
          </SelectContent>
        </Select>
      </motion.div>

      {/* Project Cards */}
      {filteredProjects.length === 0 ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-20">
          <FolderKanban size={48} className="mx-auto mb-4 text-[#D1D5DB]" />
          <p className="text-[#6B7280] font-medium">Tidak ada proyek ditemukan</p>
          <p className="text-sm text-[#9CA3AF] mt-1">Coba ubah filter pencarian Anda</p>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredProjects.map((project, idx) => {
            const sc = getStatusColor(project.status);
            return (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                onClick={() => navigate(`/projects/${project.id}`)}
                className="bg-white rounded-2xl border border-[#E5E7EB] p-5 cursor-pointer hover:shadow-lg hover:border-[#D4AF77]/40 transition-all duration-300 group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: '#EFF6FF' }}>
                    <FolderKanban size={20} style={{ color: '#0A2540' }} />
                  </div>
                  <span className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full" style={{ background: sc.bg, color: sc.text }}>
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: sc.dot }} />
                    {project.status}
                  </span>
                </div>

                <h3 className="font-semibold text-[#111827] mb-1 group-hover:text-[#0A2540] transition-colors truncate">
                  {project.name}
                </h3>
                <p className="text-sm text-[#6B7280] line-clamp-2 mb-4">{project.description}</p>

                <div className="mb-3">
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-[#6B7280]">Progress</span>
                    <span className="font-semibold" style={{ color: '#0A2540' }}>{project.progress}%</span>
                  </div>
                  <Progress value={project.progress} className="h-2 rounded-full" />
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-[#E5E7EB]">
                  <div className="flex items-center gap-2 text-xs text-[#6B7280]">
                    <Calendar size={14} />
                    <span>{new Date(project.startDate).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="flex -space-x-1.5">
                      {project.teamMembers.slice(0, 3).map(mid => {
                        const m = getUserById(mid);
                        return m ? (
                          <div key={mid} className="w-6 h-6 rounded-full border-2 border-white flex items-center justify-center text-[7px] font-bold text-white" style={{ background: '#D4AF77' }}>
                            {m.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                          </div>
                        ) : null;
                      })}
                    </div>
                    {project.teamMembers.length > 3 && (
                      <span className="text-[10px] text-[#6B7280] font-medium">+{project.teamMembers.length - 3}</span>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Projects;
