import { useState, useEffect } from "react";
import axios from "axios";

type EmployeeRank = 1 | 2 | 3 | 4;

interface Employee {
  id: number;
  name: string;
  rank: EmployeeRank;
  registered_at: string;
}

interface ProjectBase {
  title: string;
  description: string;
  parent_project_id: number | null;
  max_participants: number;
}

interface ProjectWithParticipants extends ProjectBase {
  id: number;
  created_at: string;
  employees: Employee[];
}

interface ProjectWithChildren extends ProjectWithParticipants {
  children: ProjectWithChildren[];
}

interface EmployeeList {
  employees: Employee[];
}

interface ProjectList {
  projects: ProjectWithParticipants[];
}

interface Project {
  id: number;
  title: string;
  description: string;
  parent_project_id: number | null;
  max_participants: number;
  created_at: string;
}

interface EmployeeCreate {
  name: string;
  rank: EmployeeRank;
}

interface ProjectCreate {
  title: string;
  description: string;
  parent_project_id: number | null;
  max_participants: number;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

const employeeApi = {
  getEmployees: (params?: { limit?: number; offset?: number }) =>
    api.get<EmployeeList>("/employees/", { params }),
  createEmployee: (data: EmployeeCreate) =>
    api.post<Employee>("/employees/", data),
  updateEmployee: (id: number, data: EmployeeCreate) =>
    api.put<Employee>(`/employees/${id}/`, data),
  deleteEmployee: (id: number) => api.delete(`/employees/${id}/`),
};

const projectApi = {
  getProjects: (params?: {
    limit?: number;
    offset?: number;
    search?: string;
    with_participants?: boolean;
  }) => api.get<ProjectList>("/projects/", { params }),

  getProjectWithChildren: (id: number) =>
    api.get<ProjectWithChildren>(`/projects/${id}/`),

  createProject: (data: ProjectCreate) =>
    api.post<Project>("/projects/", data),

  updateProject: (id: number, data: ProjectCreate) =>
    api.put<Project>(`/projects/${id}/`, data),

  addParticipant: (projectId: number, employeeId: number, force = false) =>
    api.post<ProjectWithParticipants>(
      `/projects/${projectId}/participants/${employeeId}/`,
      {},
      { params: { force } }
    ),

  deleteParticipant: (projectId: number, employeeId: number) =>
    api.delete<ProjectWithParticipants>(
      `/projects/${projectId}/participants/${employeeId}/`
    ),
  deleteProject: (id: number) => api.delete(`/projects/${id}/`),
};

const buildProjectTree = (
  projects: ProjectWithParticipants[],
  parentId: number | null = null
): ProjectWithChildren[] => {
  return projects
    .filter(project => project.parent_project_id === parentId)
    .map(project => ({
      ...project,
      children: buildProjectTree(projects, project.id)
    }));
};

export default function App() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [projects, setProjects] = useState<ProjectWithParticipants[]>([]);
  const [newEmployee, setNewEmployee] = useState({ name: "", rank: 1 });
  const [newProject, setNewProject] = useState<ProjectCreate>({
    title: "",
    description: "",
    parent_project_id: null,
    max_participants: 10
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        const [empResponse, projResponse] = await Promise.all([
          employeeApi.getEmployees(),
          projectApi.getProjects({ with_participants: true })
        ]);

        setEmployees(empResponse.data.employees);
        setProjects(projResponse.data.projects);
      } catch (error) {
        console.error("Error loading data:", error);
      }
    };
    loadData();
  }, []);

  const ProjectNode = ({ project }: { project: ProjectWithChildren }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [localProject, setLocalProject] = useState(project);
    const [isEditing, setIsEditing] = useState(false);
    const [editData, setEditData] = useState<ProjectCreate>({
      title: project.title,
      description: project.description,
      parent_project_id: project.parent_project_id,
      max_participants: project.max_participants
    });

    const loadFullProject = async () => {
      try {
        const response = await projectApi.getProjectWithChildren(project.id);
        setLocalProject(response.data);
      } catch (error) {
        console.error("Error loading project details:", error);
      }
    };

    const handleUpdateProject = async () => {
      try {
        const response = await projectApi.updateProject(project.id, editData);
        setLocalProject({ ...response.data, children: localProject.children } as ProjectWithChildren);
        setIsEditing(false);
        setProjects(prev =>
          prev.map(p => p.id === project.id ? response.data : p) as ProjectWithChildren[]
        );
      } catch (error) {
        console.error("Error updating project:", error);
      }
    };

    const handleAddParticipant = async (employeeId: number) => {
      try {
        const response = await projectApi.addParticipant(
          project.id,
          employeeId
        );
        setLocalProject(prev => ({
          ...prev,
          employees: response.data.employees
        }));
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 400) {
          if (window.confirm(`${error.response.data.detail} Все равно добавить?`)) {
            const response = await projectApi.addParticipant(
              project.id,
              employeeId,
              true
            );
            setLocalProject(prev => ({
              ...prev,
              employees: response.data.employees
            }));
          }
        }
      }
    };

    const handleRemoveParticipant = async (employeeId: number) => {
      try {
        await projectApi.deleteParticipant(
          project.id,
          employeeId
        );
        setLocalProject(prev => ({
          ...prev,
          employees: prev.employees.filter(e => e.id !== employeeId)
        }));
      } catch (error) {
        console.error(error);
      }
    };

    return (
      <div style={{ marginLeft: 20, borderLeft: "1px solid #ccc", paddingLeft: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <button onClick={() => {
            if (!isExpanded) loadFullProject();
            setIsExpanded(!isExpanded);
          }}>
            {isExpanded ? "▼" : "▶"}
          </button>

          {isEditing ? (
            <input
              value={editData.title}
              onChange={e => setEditData({...editData, title: e.target.value})}
            />
          ) : (
            <h3>{localProject.title}</h3>
          )}

          <span>({localProject.employees ? localProject.employees.length : 0}/{localProject.max_participants})</span>

          <button onClick={() => setIsEditing(!isEditing)}>
            {isEditing ? "Отмена" : "✎"}
          </button>

          {isEditing && (
            <button onClick={handleUpdateProject}>Сохранить</button>

          )}
          {isEditing && (
            <button onClick={async () => {
              await projectApi.deleteProject(project.id);
              setProjects(prev => prev.filter(e => e.id !== project.id));
            }}>
              Удалить
            </button>
          )}
        </div>

        {isExpanded && (
          <div style={{ marginTop: 10 }}>
            {isEditing ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <textarea
                  value={editData.description}
                  onChange={e => setEditData({...editData, description: e.target.value})}
                />
                <input
                  type="number"
                  value={editData.max_participants}
                  onChange={e => setEditData({...editData, max_participants: Number(e.target.value)})}
                />
                <select
                  value={editData.parent_project_id ?? ""}
                  onChange={e => setEditData({
                    ...editData,
                    parent_project_id: e.target.value ? Number(e.target.value) : null
                  })}
                >
                  <option value="">Нет родительского проекта</option>
                  {projects
                    .filter(p => p.id !== project.id)
                    .map(p => (
                      <option key={p.id} value={p.id}>{p.title}</option>
                    ))}
                </select>
              </div>
            ) : (
              <>
                <p>{localProject.description}</p>

                <div>
                  <h4>Участники:</h4>
                  <select
                    onChange={e => handleAddParticipant(Number(e.target.value))}
                    style={{ marginBottom: 10 }}
                  >
                    <option value="">Выбрать сотрудника</option>
                    {employees.map(e => (
                      <option key={e.id} value={e.id}>
                        {e.name} (Ранг {e.rank})
                      </option>
                    ))}
                  </select>

                  <ul style={{ listStyle: "none", padding: 0 }}>
                    {localProject.employees && localProject.employees.map(employee => (
                      <li
                        key={employee.id}
                        style={{ display: "flex", gap: 10, alignItems: "center" }}
                      >
                        {employee.name}
                        <button onClick={() => handleRemoveParticipant(employee.id)}>
                          ×
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>

                {localProject.children?.length > 0 && (
                  <div>
                    <h4>Подпроекты:</h4>
                    {localProject.children.map(child => (
                      <ProjectNode key={child.id} project={child} />
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
      <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
      <h1>Управление проектами</h1>

      {/* Работа с сотрудниками */}
      <section style={{ marginBottom: 40 }}>
        <h2>Сотрудники</h2>
        <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
          <input
            type="text"
            placeholder="Имя сотрудника"
            value={newEmployee.name}
            onChange={e => setNewEmployee({ ...newEmployee, name: e.target.value })}
            style={{ flexGrow: 1 }}
          />
          <select
            value={newEmployee.rank}
            onChange={e => setNewEmployee({
              ...newEmployee,
              rank: Number(e.target.value) as EmployeeRank
            })}
          >
            {[1, 2, 3, 4].map(rank => (
              <option key={rank} value={rank}>Ранг {rank}</option>
            ))}
          </select>
          <button onClick={async () => {
            try {
              const response = await employeeApi.createEmployee(newEmployee as EmployeeCreate);
              setEmployees([...employees, response.data]);
              setNewEmployee({ name: "", rank: 1 });
            } catch (error) {
              console.error("Ошибка создания сотрудника:", error);
            }
          }}>
            Добавить
          </button>
        </div>

        <ul style={{ padding: 0 }}>
          {employees.map(employee => (
            <li
              key={employee.id}
              style={{
                display: "flex",
                gap: 10,
                alignItems: "center",
                marginBottom: 5
              }}
            >
              <input
                value={employee.name}
                onChange={e => {
                  const newEmployees = [...employees];
                  const index = newEmployees.findIndex(e => e.id === employee.id);
                  newEmployees[index].name = e.target.value;
                  setEmployees(newEmployees);
                }}
              />
              <select
                value={employee.rank}
                onChange={e => {
                  const newEmployees = [...employees];
                  const index = newEmployees.findIndex(e => e.id === employee.id);
                  newEmployees[index].rank = Number(e.target.value) as EmployeeRank;
                  setEmployees(newEmployees);
                }}
              >
                {[1, 2, 3, 4].map(rank => (
                  <option key={rank} value={rank}>Ранг {rank}</option>
                ))}
              </select>
              <button onClick={async () => {
                try {
                  await employeeApi.updateEmployee(employee.id, {
                    name: employee.name,
                    rank: employee.rank
                  });
                } catch (error) {
                  console.error("Ошибка обновления сотрудника:", error);
                }
              }}>
                Сохранить
              </button>
              <button onClick={async () => {
                await employeeApi.deleteEmployee(employee.id);
                setEmployees(prev => prev.filter(e => e.id !== employee.id));
              }}>
                Удалить
              </button>
            </li>
          ))}
        </ul>
      </section>

      {/* Создание проекта */}
      <section style={{ marginBottom: 40 }}>
        <h2>Создать проект</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <input
            type="text"
            placeholder="Название проекта"
            value={newProject.title}
            onChange={e => setNewProject({ ...newProject, title: e.target.value })}
          />
          <textarea
            placeholder="Описание проекта"
            value={newProject.description}
            onChange={e => setNewProject({ ...newProject, description: e.target.value })}
          />
          <input
            type="number"
            placeholder="Макс. участников"
            value={newProject.max_participants}
            onChange={e => setNewProject({
              ...newProject,
              max_participants: Number(e.target.value)
            })}
          />
          <select
            value={newProject.parent_project_id ?? ""}
            onChange={e => setNewProject({
              ...newProject,
              parent_project_id: e.target.value ? Number(e.target.value) : null
            })}
          >
            <option value="">Без родительского проекта</option>
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.title}</option>
            ))}
          </select>
          <button onClick={async () => {
            try {
              const response = await projectApi.createProject(newProject);
              setProjects([...projects, response.data] as ProjectWithChildren[]);
              setNewProject({
                title: "",
                description: "",
                parent_project_id: null,
                max_participants: 10
              });
            } catch (error) {
              console.error("Ошибка создания проекта:", error);
            }
          }}>
            Создать проект
          </button>
        </div>
      </section>

      {/* Project Hierarchy */}
      <section>
        <h2>Иерархия проектов</h2>
        <div>
          {buildProjectTree(projects)
            .filter(p => !p.parent_project_id)
            .map(project => (
              <ProjectNode key={project.id} project={project} />
            ))}
        </div>
      </section>
    </div>
  );
}
