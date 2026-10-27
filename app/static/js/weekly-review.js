export function dateKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

export function buildWeeklyReview(tasks, start, today = new Date()) {
  const first = dateKey(start);
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  const last = dateKey(end);
  const nextDays = Array.from({ length: 7 }, (_, index) => {
    const day = new Date(start);
    day.setDate(day.getDate() + 7 + index);
    return dateKey(day);
  });
  const inWeek = key => key >= first && key <= last;
  const planned = tasks.filter(task => inWeek(task.due_date));
  const completed = tasks.filter(task => {
    if (task.status !== "completed" || !task.completed_at) return false;
    const timestamp = new Date(task.completed_at);
    return !Number.isNaN(timestamp.getTime()) && inWeek(dateKey(timestamp));
  });
  const pending = planned.filter(task => task.status !== "completed");
  const backlog = tasks.filter(task => task.status !== "completed" && task.due_date < first);
  const upcoming = tasks.filter(task => task.status !== "completed" && task.due_date >= nextDays[0] && task.due_date <= nextDays[6]);
  const groups = new Map();
  completed.forEach(task => {
    const key = task.subject_id || task.subject_name || "Sem disciplina";
    const group = groups.get(key) || { name: task.subject_name || "Sem disciplina", count: 0 };
    group.count += 1;
    groups.set(key, group);
  });
  const load = new Map(nextDays.map(day => [day, upcoming.filter(task => task.due_date === day).length]));
  const candidates = [...backlog, ...pending, ...upcoming].sort((a, b) => a.due_date.localeCompare(b.due_date) || (b.difficulty || 3) - (a.difficulty || 3) || a.title.localeCompare(b.title));
  const proposal = candidates.slice(0, 3).map(task => {
    const eligible = nextDays.filter(day => day <= task.due_date);
    const options = eligible.length ? eligible : nextDays;
    const day = [...options].sort((a, b) => load.get(a) - load.get(b) || a.localeCompare(b))[0];
    load.set(day, load.get(day) + 1);
    return { task, day, minutes: Math.min(25, task.estimated_minutes || 30), overdue: task.due_date < day };
  });
  return { first, last, nextDays, planned, completed, pending, backlog, upcoming, groups: [...groups.values()], proposal, future: first > dateKey(today), historical: last < dateKey(today) };
}
