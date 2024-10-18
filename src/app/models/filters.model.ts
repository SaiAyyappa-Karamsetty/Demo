export class Filters {
    private filters: {};

    constructor() {
        this.filters = {};
    }

    getFilters() {
        return this.filters;
    }

    // Add filters to the filters object, return 0 if successful, -1 if not
    addFilters(filters: {}): number {
        if (filters['category'] != undefined || this.filters['category'] != undefined) {
            for (let key in Object.keys(filters)) {
                this.filters[key] = filters[key];
                return 0;
            }
        }
        console.error("Filters must have a category");
        return -1;
    }

    clearFilters() {
        this.filters = {};
    }

    clearFilter(key: string) {
        delete this.filters[key];
    }
}