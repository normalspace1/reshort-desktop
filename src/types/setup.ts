export interface PreflightItem {
	id: string
	ok: boolean
	detail: string
}

export interface PreflightCheck extends PreflightItem {
	label: string
}
