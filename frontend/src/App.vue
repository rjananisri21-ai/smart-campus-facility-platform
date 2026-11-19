<script setup>
import { ref, computed } from 'vue'

const currentPage = ref('Dashboard')
const loggedIn = ref(false)
const username = ref('Janani')
const search = ref('')
const selectedFacility = ref(null)

const menu = [
  'Dashboard',
  'Facilities',
  'Bookings',
  'Maintenance',
  'Approvals',
  'Admin'
]

const facilities = ref([
  { id: 1, name: 'Computer Lab 1', type: 'Laboratory', location: 'Block A', capacity: 40, status: 'Available' },
  { id: 2, name: 'Seminar Hall', type: 'Hall', location: 'Block B', capacity: 120, status: 'Available' },
  { id: 3, name: 'Smart Classroom', type: 'Classroom', location: 'Block C', capacity: 60, status: 'Available' },
  { id: 4, name: 'Physics Lab', type: 'Laboratory', location: 'Block D', capacity: 30, status: 'Maintenance' }
])

const bookings = ref([
  { id: 101, facility: 'Computer Lab 1', date: '2026-11-20', time: '10:00 AM', status: 'Approved', user: 'Janani' },
  { id: 102, facility: 'Seminar Hall', date: '2026-11-21', time: '02:00 PM', status: 'Pending', user: 'Arun' }
])

const tickets = ref([
  { id: 201, issue: 'Projector not working', location: 'Seminar Hall', priority: 'High', status: 'New', assigned: 'Not assigned' },
  { id: 202, issue: 'Air conditioner issue', location: 'Computer Lab 1', priority: 'Medium', status: 'Assigned', assigned: 'Technician 1' }
])

const filteredFacilities = computed(() =>
  facilities.value.filter(f =>
    f.name.toLowerCase().includes(search.value.toLowerCase())
  )
)

function bookFacility(facility) {
  selectedFacility.value = facility
  currentPage.value = 'New Booking'
}

function submitBooking() {
  if (!selectedFacility.value) return
  const date = document.getElementById('booking-date')?.value
  const time = document.getElementById('booking-time')?.value
  if (!date || !time) {
    alert('Please select a date and time')
    return
  }

  bookings.value.push({
    id: Date.now(),
    facility: selectedFacility.value.name,
    date,
    time,
    status: 'Pending',
    user: username.value
  })

  selectedFacility.value = null
  currentPage.value = 'Bookings'
  alert('Booking request submitted successfully!')
}

function addTicket() {
  const issue = document.getElementById('issue')?.value
  const location = document.getElementById('ticket-location')?.value
  const priority = document.getElementById('priority')?.value

  if (!issue || !location) {
    alert('Please enter issue details')
    return
  }

  tickets.value.push({
    id: Date.now(),
    issue,
    location,
    priority,
    status: 'New',
    assigned: 'Not assigned'
  })

  currentPage.value = 'Maintenance'
  alert('Maintenance ticket created successfully!')
}

function approveBooking(id, status) {
  const booking = bookings.value.find(b => b.id === id)
  if (booking) booking.status = status
}

function updateTicket(ticket, status) {
  ticket.status = status
}

function logout() {
  loggedIn.value = false
  currentPage.value = 'Dashboard'
}

const pendingBookings = computed(() =>
  bookings.value.filter(b => b.status === 'Pending').length
)

const openTickets = computed(() =>
  tickets.value.filter(t => t.status !== 'Closed').length
)
</script>

<template>
  <!-- LOGIN PAGE -->
  <div v-if="!loggedIn" class="login-screen">
    <div class="login-card">
      <div class="logo">🎓</div>
      <h1>Smart Campus</h1>
      <p>Facility & Maintenance Management</p>

      <form @submit.prevent="loggedIn = true">
        <label>Username</label>
        <input v-model="username" placeholder="Enter username" required />

        <label>Password</label>
        <input type="password" placeholder="Enter password" required />

        <button class="primary full">Login to Dashboard →</button>
      </form>
      <small>Demo login: Enter any username and password.</small>
    </div>
  </div>

  <!-- MAIN APPLICATION -->
  <div v-else class="app-layout">

    <aside class="sidebar">
      <div class="brand">
        <span>🎓</span>
        <div>
          <strong>Smart Campus</strong>
          <small>Management Portal</small>
        </div>
      </div>

      <p class="nav-label">MAIN MENU</p>

      <button
        v-for="item in menu"
        :key="item"
        @click="currentPage = item"
        :class="{ active: currentPage === item }"
        class="nav-item"
      >
        <span>
          {{ {
            Dashboard:'▦',
            Facilities:'🏢',
            Bookings:'📅',
            Maintenance:'🔧',
            Approvals:'✓',
            Admin:'⚙'
          }[item] }}
        </span>
        {{ item }}
      </button>

      <div class="sidebar-bottom">
        <div class="profile">
          <div class="avatar">{{ username.charAt(0).toUpperCase() }}</div>
          <div>
            <strong>{{ username }}</strong>
            <small>Campus User</small>
          </div>
        </div>
        <button class="logout" @click="logout">↪ Logout</button>
      </div>
    </aside>

    <main class="main-content">

      <header class="topbar">
        <div>
          <h2>{{ currentPage }}</h2>
          <p>Smart Campus / {{ currentPage }}</p>
        </div>
        <div class="top-right">
          <span>🔔 Notifications</span>
          <div class="avatar">{{ username.charAt(0).toUpperCase() }}</div>
        </div>
      </header>

      <!-- DASHBOARD -->
      <section v-if="currentPage === 'Dashboard'">
        <div class="welcome">
          <div>
            <h1>Welcome back, {{ username }}! 👋</h1>
            <p>Here's what's happening around your campus today.</p>
          </div>
          <button class="primary" @click="currentPage='Facilities'">
            + New Booking
          </button>
        </div>

        <div class="stats">
          <div class="stat-card purple">
            <span>🏢 Total Facilities</span>
            <h1>{{ facilities.length }}</h1>
            <small>Campus facilities</small>
          </div>
          <div class="stat-card blue">
            <span>📅 Total Bookings</span>
            <h1>{{ bookings.length }}</h1>
            <small>All booking requests</small>
          </div>
          <div class="stat-card orange">
            <span>⏳ Pending Approvals</span>
            <h1>{{ pendingBookings }}</h1>
            <small>Awaiting approval</small>
          </div>
          <div class="stat-card green">
            <span>🔧 Open Tickets</span>
            <h1>{{ openTickets }}</h1>
            <small>Maintenance requests</small>
          </div>
        </div>

        <div class="content-grid">
          <div class="panel">
            <h3>Recent Bookings</h3>
            <div v-for="b in bookings.slice(-4).reverse()" :key="b.id" class="list-row">
              <div>
                <strong>{{ b.facility }}</strong>
                <small>{{ b.date }} · {{ b.time }}</small>
              </div>
              <span class="status" :class="b.status.toLowerCase()">{{ b.status }}</span>
            </div>
          </div>

          <div class="panel">
            <h3>Maintenance Overview</h3>
            <div v-for="t in tickets.slice(-4).reverse()" :key="t.id" class="list-row">
              <div>
                <strong>{{ t.issue }}</strong>
                <small>{{ t.location }}</small>
              </div>
              <span class="status" :class="t.status.toLowerCase()">{{ t.status }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- FACILITIES -->
      <section v-if="currentPage === 'Facilities'">
        <div class="section-heading">
          <div>
            <h1>Facility Catalogue</h1>
            <p>Explore and reserve campus facilities.</p>
          </div>
          <input v-model="search" placeholder="Search facilities..." />
        </div>

        <div class="facility-grid">
          <div v-for="f in filteredFacilities" :key="f.id" class="facility-card">
            <div class="facility-icon">🏢</div>
            <span class="status" :class="f.status.toLowerCase()">{{ f.status }}</span>
            <h3>{{ f.name }}</h3>
            <p>{{ f.type }} · {{ f.location }}</p>
            <p>👥 Capacity: {{ f.capacity }} people</p>
            <button
              class="primary full"
              :disabled="f.status !== 'Available'"
              @click="bookFacility(f)"
            >
              {{ f.status === 'Available' ? 'Book Facility →' : 'Unavailable' }}
            </button>
          </div>
        </div>
      </section>

      <!-- NEW BOOKING -->
      <section v-if="currentPage === 'New Booking'">
        <div class="panel form-panel">
          <h1>New Facility Booking</h1>
          <p>Submit your facility reservation request.</p>

          <label>Selected Facility</label>
          <input :value="selectedFacility?.name || ''" readonly />

          <label>Booking Date</label>
          <input id="booking-date" type="date" required />

          <label>Booking Time</label>
          <select id="booking-time">
            <option value="">Select time</option>
            <option>09:00 AM</option>
            <option>10:00 AM</option>
            <option>11:00 AM</option>
            <option>02:00 PM</option>
            <option>03:00 PM</option>
          </select>

          <button class="primary full" @click="submitBooking">
            Submit Booking Request
          </button>
          <button class="secondary full" @click="currentPage='Facilities'">
            Cancel
          </button>
        </div>
      </section>

      <!-- BOOKINGS -->
      <section v-if="currentPage === 'Bookings'">
        <h1>Booking Management</h1>
        <p>View your facility reservation requests.</p>

        <div class="panel table-panel">
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Facility</th><th>Date</th>
                <th>Time</th><th>User</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in bookings" :key="b.id">
                <td>{{ b.id }}</td>
                <td>{{ b.facility }}</td>
                <td>{{ b.date }}</td>
                <td>{{ b.time }}</td>
                <td>{{ b.user }}</td>
                <td><span class="status" :class="b.status.toLowerCase()">{{ b.status }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- MAINTENANCE -->
      <section v-if="currentPage === 'Maintenance'">
        <div class="section-heading">
          <div>
            <h1>Maintenance Management</h1>
            <p>Report and track campus maintenance issues.</p>
          </div>
        </div>

        <div class="panel form-panel">
          <h3>Create Maintenance Ticket</h3>
          <label>Issue Description</label>
          <input id="issue" placeholder="Example: Projector not working" />

          <label>Facility Location</label>
          <select id="ticket-location">
            <option value="">Select facility</option>
            <option v-for="f in facilities" :key="f.id">{{ f.name }}</option>
          </select>

          <label>Priority</label>
          <select id="priority">
            <option>Low</option>
            <option>Medium</option>
            <option>High</option>
          </select>

          <button class="primary full" @click="addTicket">+ Create Ticket</button>
        </div>

        <div class="panel table-panel">
          <h3>Maintenance Queue</h3>
          <table>
            <thead>
              <tr><th>Ticket</th><th>Issue</th><th>Location</th><th>Priority</th><th>Status</th><th>Update</th></tr>
            </thead>
            <tbody>
              <tr v-for="t in tickets" :key="t.id">
                <td>#{{ t.id }}</td>
                <td>{{ t.issue }}</td>
                <td>{{ t.location }}</td>
                <td>{{ t.priority }}</td>
                <td>{{ t.status }}</td>
                <td>
                  <select :value="t.status" @change="updateTicket(t, $event.target.value)">
                    <option>New</option>
                    <option>Assigned</option>
                    <option>In Progress</option>
                    <option>Closed</option>
                  </select>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- APPROVALS -->
      <section v-if="currentPage === 'Approvals'">
        <h1>Booking Approvals</h1>
        <p>Review and approve pending facility requests.</p>

        <div class="panel table-panel">
          <table>
            <thead>
              <tr><th>ID</th><th>Facility</th><th>User</th><th>Date</th><th>Status</th><th>Action</th></tr>
            </thead>
            <tbody>
              <tr v-for="b in bookings" :key="b.id">
                <td>{{ b.id }}</td>
                <td>{{ b.facility }}</td>
                <td>{{ b.user }}</td>
                <td>{{ b.date }}</td>
                <td>{{ b.status }}</td>
                <td v-if="b.status === 'Pending'">
                  <button class="approve" @click="approveBooking(b.id,'Approved')">Approve</button>
                  <button class="reject" @click="approveBooking(b.id,'Rejected')">Reject</button>
                </td>
                <td v-else>Completed</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ADMIN -->
      <section v-if="currentPage === 'Admin'">
        <h1>Administrator Dashboard</h1>
        <p>Campus operations overview.</p>

        <div class="stats">
          <div class="stat-card purple"><span>Facilities</span><h1>{{ facilities.length }}</h1></div>
          <div class="stat-card blue"><span>Bookings</span><h1>{{ bookings.length }}</h1></div>
          <div class="stat-card orange"><span>Pending</span><h1>{{ pendingBookings }}</h1></div>
          <div class="stat-card green"><span>Tickets</span><h1>{{ tickets.length }}</h1></div>
        </div>

        <div class="panel">
          <h3>Facility Status</h3>
          <div v-for="f in facilities" :key="f.id" class="list-row">
            <div>
              <strong>{{ f.name }}</strong>
              <small>{{ f.location }}</small>
            </div>
            <span class="status" :class="f.status.toLowerCase()">{{ f.status }}</span>
          </div>
        </div>
      </section>

    </main>
  </div>
</template>

<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: Arial, sans-serif; background: #f4f6fb; color: #202b40; }
button, input, select { font: inherit; }
button { cursor: pointer; }

.login-screen {
  min-height: 100vh; display: grid; place-items: center;
  background: linear-gradient(135deg,#172554,#4f46e5,#9333ea);
  padding: 20px;
}
.login-card {
  background: white; padding: 40px; border-radius: 22px;
  width: min(420px,100%); box-shadow: 0 20px 60px #11182755;
}
.login-card h1 { text-align: center; margin-bottom: 8px; }
.login-card p, .login-card small { color: #7b8497; text-align: center; display: block; }
.logo { text-align: center; font-size: 48px; }
.login-card form { margin-top: 28px; }

.app-layout { min-height: 100vh; }
.sidebar {
  position: fixed; inset: 0 auto 0 0; width: 245px;
  background: #172554; color: white; padding: 25px 17px;
  display: flex; flex-direction: column; z-index: 2;
}
.brand { display: flex; gap: 12px; align-items: center; margin-bottom: 45px; }
.brand span { font-size: 32px; }
.brand strong, .brand small, .profile strong, .profile small { display: block; }
.brand small, .profile small { color: #b7c5e4; margin-top: 5px; font-size: 11px; }
.nav-label { color: #8fa1c6; font-size: 11px; letter-spacing: 2px; }
.nav-item {
  border: 0; padding: 14px; text-align: left; color: #d8e1f5;
  background: transparent; border-radius: 9px; margin: 4px 0;
}
.nav-item span { margin-right: 12px; }
.nav-item.active, .nav-item:hover { background: #374b84; color: white; }
.sidebar-bottom { margin-top: auto; }
.profile { display: flex; align-items: center; gap: 12px; padding: 12px 0; }
.avatar {
  width: 36px; height: 36px; display: grid; place-items: center;
  border-radius: 50%; background: #c4b5fd; color: #312e81; font-weight: bold;
}
.logout { width: 100%; padding: 12px; background: #263965; color: white; border: 0; border-radius: 8px; }

.main-content { margin-left: 245px; padding: 28px 35px; }
.topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
.topbar h2 { margin: 0; }
.topbar p, .welcome p, .section-heading p { color: #8490a4; margin-top: 7px; }
.top-right { display: flex; align-items: center; gap: 18px; }
.welcome, .section-heading { display: flex; justify-content: space-between; align-items: center; gap: 15px; margin-bottom: 25px; }
.welcome h1, .section-heading h1 { margin-bottom: 5px; }

.primary, .secondary, .approve, .reject {
  border: 0; border-radius: 8px; padding: 12px 17px; font-weight: bold;
}
.primary { background: #4f46e5; color: white; }
.primary:hover { background: #3730a3; }
.primary:disabled { opacity: .5; cursor: not-allowed; }
.secondary { background: #e7e9f4; color: #343d56; margin-top: 10px; }
.full { width: 100%; margin-top: 16px; }
.approve { background: #dcfce7; color: #166534; padding: 8px; }
.reject { background: #fee2e2; color: #991b1b; padding: 8px; margin-left: 5px; }

.stats { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 17px; margin-bottom: 25px; }
.stat-card { padding: 23px; border-radius: 14px; background: white; box-shadow: 0 4px 15px #1e293b08; }
.stat-card h1 { margin: 17px 0 5px; font-size: 34px; }
.stat-card small { color: #8490a4; }
.purple { border-top: 4px solid #8b5cf6; }
.blue { border-top: 4px solid #3b82f6; }
.orange { border-top: 4px solid #f59e0b; }
.green { border-top: 4px solid #10b981; }

.content-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.panel, .facility-card {
  background: white; border-radius: 14px; padding: 22px;
  margin-bottom: 20px; box-shadow: 0 4px 20px #1e293b08;
}
.panel h3 { margin-top: 0; }
.list-row { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid #edf0f5; gap: 10px; }
.list-row:last-child { border: 0; }
.list-row small { display: block; color: #8490a4; margin-top: 7px; }

.status { padding: 6px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; white-space: nowrap; }
.approved, .available, .closed { background: #dcfce7; color: #166534; }
.pending, .assigned { background: #fef3c7; color: #92400e; }
.rejected, .maintenance { background: #fee2e2; color: #991b1b; }
.new { background: #dbeafe; color: #1d4ed8; }
.in.progress { background: #ede9fe; color: #5b21b6; }

.facility-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 20px; }
.facility-card { position: relative; }
.facility-icon { font-size: 38px; margin-bottom: 15px; }
.facility-card h3 { margin-bottom: 8px; }
.facility-card p { color: #8490a4; font-size: 13px; }
.facility-card .status { position: absolute; top: 20px; right: 15px; }

.form-panel { max-width: 650px; }
label { display: block; font-weight: bold; margin: 18px 0 8px; font-size: 13px; }
input, select {
  width: 100%; padding: 12px; border: 1px solid #dce1eb;
  border-radius: 8px; background: white; outline: none;
}
input:focus, select:focus { border-color: #4f46e5; }
.table-panel { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 650px; }
th, td { padding: 14px 12px; text-align: left; border-bottom: 1px solid #edf0f5; font-size: 13px; }
th { color: #77839a; background: #f8f9fc; }

@media(max-width:1000px) {
  .stats { grid-template-columns: repeat(2,1fr); }
  .facility-grid { grid-template-columns: repeat(2,1fr); }
}
@media(max-width:700px) {
  .sidebar { position: relative; width: 100%; }
  .sidebar-bottom { margin-top: 15px; }
  .main-content { margin-left: 0; padding: 18px; }
  .content-grid, .facility-grid, .stats { grid-template-columns: 1fr; }
  .welcome, .section-heading { align-items: flex-start; flex-direction: column; }
  .topbar { gap: 10px; }
}
</style>