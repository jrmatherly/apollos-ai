import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
	// UI state
	isOpen: false,
	activeTab: "orgs",
	loading: false,
	error: null,

	// Data
	orgs: [],
	teams: [],
	users: [],
	groupMappings: [],
	vaultKeys: [],

	// Selection state
	selectedOrgId: null,
	selectedTeamId: null,

	// Form state
	editingItem: null,
	showForm: false,

	// Tab definitions
	tabs: [
		{ id: "orgs", label: "Organizations" },
		{ id: "teams", label: "Teams" },
		{ id: "users", label: "Users" },
		{ id: "groups", label: "Group Mappings" },
		{ id: "keys", label: "API Keys" },
		{ id: "services", label: "MCP Services" },
	],

	// ---------- Panel open/close ----------

	open() {
		this.isOpen = true;
		this.loadOrgs();
	},

	close() {
		this.isOpen = false;
		this.editingItem = null;
		this.showForm = false;
	},

	setTab(tab) {
		this.activeTab = tab;
		this.editingItem = null;
		this.showForm = false;
		this.error = null;
		if (tab === "orgs") this.loadOrgs();
		else if (tab === "teams" && this.selectedOrgId)
			this.loadTeams(this.selectedOrgId);
		else if (tab === "users") this.loadUsers();
		else if (tab === "groups" && this.selectedOrgId)
			this.loadGroupMappings(this.selectedOrgId);
		else if (tab === "keys") this.loadVaultKeys();
	},

	// ---------- Organizations ----------

	async loadOrgs() {
		this.loading = true;
		try {
			const res = await callJsonApi("/admin_orgs", { action: "list" });
			this.orgs = res.data || [];
		} catch (e) {
			this.error = e.message;
		}
		this.loading = false;
	},

	async createOrg(name, slug) {
		try {
			await callJsonApi("/admin_orgs", { action: "create", name, slug });
			this.showForm = false;
			await this.loadOrgs();
		} catch (e) {
			this.error = e.message;
		}
	},

	async updateOrg(orgId, data) {
		try {
			await callJsonApi("/admin_orgs", {
				action: "update",
				org_id: orgId,
				...data,
			});
			this.editingItem = null;
			await this.loadOrgs();
		} catch (e) {
			this.error = e.message;
		}
	},

	async deactivateOrg(orgId) {
		if (!confirm("Deactivate this organization? Members will lose access."))
			return;
		try {
			await callJsonApi("/admin_orgs", { action: "deactivate", org_id: orgId });
			await this.loadOrgs();
		} catch (e) {
			this.error = e.message;
		}
	},

	selectOrg(orgId) {
		this.selectedOrgId = orgId;
	},

	// ---------- Teams ----------

	async loadTeams(orgId) {
		this.loading = true;
		try {
			const res = await callJsonApi("/admin_teams", {
				action: "list",
				org_id: orgId,
			});
			this.teams = res.data || [];
		} catch (e) {
			this.error = e.message;
		}
		this.loading = false;
	},

	async createTeam(orgId, name, slug) {
		try {
			await callJsonApi("/admin_teams", {
				action: "create",
				org_id: orgId,
				name,
				slug,
			});
			this.showForm = false;
			await this.loadTeams(orgId);
		} catch (e) {
			this.error = e.message;
		}
	},

	async updateTeam(teamId, data) {
		try {
			await callJsonApi("/admin_teams", {
				action: "update",
				team_id: teamId,
				...data,
			});
			this.editingItem = null;
			if (this.selectedOrgId) await this.loadTeams(this.selectedOrgId);
		} catch (e) {
			this.error = e.message;
		}
	},

	async deleteTeam(teamId) {
		if (!confirm("Delete this team? This cannot be undone.")) return;
		try {
			await callJsonApi("/admin_teams", { action: "delete", team_id: teamId });
			if (this.selectedOrgId) await this.loadTeams(this.selectedOrgId);
		} catch (e) {
			this.error = e.message;
		}
	},

	// ---------- Users ----------

	async loadUsers() {
		this.loading = true;
		try {
			const params = { action: "list" };
			if (this.selectedOrgId) params.org_id = this.selectedOrgId;
			const res = await callJsonApi("/admin_users", params);
			this.users = res.data || [];
		} catch (e) {
			this.error = e.message;
		}
		this.loading = false;
	},

	async inviteUser(email, password, displayName, orgId, teamId, role) {
		try {
			await callJsonApi("/admin_users", {
				action: "invite",
				email,
				password,
				display_name: displayName,
				org_id: orgId,
				team_id: teamId,
				role,
			});
			this.showForm = false;
			await this.loadUsers();
		} catch (e) {
			this.error = e.message;
		}
	},

	async updateUserRole(userId, orgId, teamId, role) {
		try {
			await callJsonApi("/admin_users", {
				action: "update_role",
				user_id: userId,
				org_id: orgId,
				team_id: teamId,
				role,
			});
			await this.loadUsers();
		} catch (e) {
			this.error = e.message;
		}
	},

	async deactivateUser(userId) {
		if (!confirm("Deactivate this user?")) return;
		try {
			await callJsonApi("/admin_users", {
				action: "deactivate",
				user_id: userId,
			});
			await this.loadUsers();
		} catch (e) {
			this.error = e.message;
		}
	},

	// ---------- Group Mappings ----------

	async loadGroupMappings(orgId) {
		this.loading = true;
		try {
			const res = await callJsonApi("/admin_group_mappings", {
				action: "list",
				org_id: orgId,
			});
			this.groupMappings = res.data || [];
		} catch (e) {
			this.error = e.message;
		}
		this.loading = false;
	},

	async upsertGroupMapping(entraGroupId, orgId, teamId, role) {
		try {
			await callJsonApi("/admin_group_mappings", {
				action: "upsert",
				entra_group_id: entraGroupId,
				org_id: orgId,
				team_id: teamId,
				role,
			});
			this.showForm = false;
			if (orgId) await this.loadGroupMappings(orgId);
		} catch (e) {
			this.error = e.message;
		}
	},

	async deleteGroupMapping(entraGroupId) {
		if (!confirm("Delete this group mapping?")) return;
		try {
			await callJsonApi("/admin_group_mappings", {
				action: "delete",
				entra_group_id: entraGroupId,
			});
			if (this.selectedOrgId) await this.loadGroupMappings(this.selectedOrgId);
		} catch (e) {
			this.error = e.message;
		}
	},

	// ---------- API Key Vault ----------

	async loadVaultKeys() {
		this.loading = true;
		try {
			const ownerType = this.selectedOrgId ? "org" : "system";
			const ownerId = this.selectedOrgId || "system";
			const res = await callJsonApi("/admin_api_keys", {
				action: "list",
				owner_type: ownerType,
				owner_id: ownerId,
			});
			this.vaultKeys = res.data || [];
		} catch (e) {
			this.error = e.message;
		}
		this.loading = false;
	},

	async storeVaultKey(ownerType, ownerId, keyName, value) {
		try {
			await callJsonApi("/admin_api_keys", {
				action: "store",
				owner_type: ownerType,
				owner_id: ownerId,
				key_name: keyName,
				value,
			});
			this.showForm = false;
			await this.loadVaultKeys();
		} catch (e) {
			this.error = e.message;
		}
	},

	async deleteVaultKey(vaultId) {
		if (!confirm("Delete this API key?")) return;
		try {
			await callJsonApi("/admin_api_keys", {
				action: "delete",
				vault_id: vaultId,
			});
			await this.loadVaultKeys();
		} catch (e) {
			this.error = e.message;
		}
	},
};

export const store = createStore("admin", model);
